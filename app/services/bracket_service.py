"""Avanço automático do mata-mata: propaga vencedor/perdedor e preenche as 32avas."""
import csv
from pathlib import Path

from sqlmodel import Session, select

from app.domain.enums import FasePartida, StatusPartida, TipoOrigem
from app.domain.models import Grupo, Partida
from app.repositories import match_repo
from app.services import standings_service

MAPEAMENTO_PATH = Path(__file__).resolve().parents[2] / "data" / "mapeamento_terceiros.csv"
VENCEDORES_3O = ["1A", "1B", "1D", "1E", "1G", "1I", "1K", "1L"]


def vencedor_perdedor(partida: Partida) -> tuple[int | None, int | None]:
    """Retorna (vencedor_id, perdedor_id) de um jogo de mata-mata finalizado.

    Placar conta apenas os 90 min; em empate, o classificado define o vencedor.
    """
    if partida.placar_mandante is None or partida.placar_visitante is None:
        return None, None
    if partida.placar_mandante > partida.placar_visitante:
        return partida.mandante_id, partida.visitante_id
    if partida.placar_visitante > partida.placar_mandante:
        return partida.visitante_id, partida.mandante_id
    # Empate nos 90 min → classificado decide
    venc = partida.classificado_id
    if venc is None:
        return None, None
    perd = partida.mandante_id if venc == partida.visitante_id else partida.visitante_id
    return venc, perd


def avancar(session: Session, partida_id: int) -> list[Partida]:
    """Propaga o resultado de um jogo de mata-mata para os jogos que dependem dele."""
    partida = match_repo.get(session, partida_id)
    if partida is None or partida.fase == FasePartida.GRUPOS:
        return []
    venc, perd = vencedor_perdedor(partida)
    if venc is None:
        return []

    proximas = session.exec(
        select(Partida).where(
            (Partida.origem_mandante_id == partida_id)
            | (Partida.origem_visitante_id == partida_id)
        )
    ).all()

    atualizadas: list[Partida] = []
    for prox in proximas:
        mudou = False
        if prox.origem_mandante_id == partida_id:
            prox.mandante_id = venc if prox.origem_mandante_tipo == TipoOrigem.VENCEDOR else perd
            mudou = True
        if prox.origem_visitante_id == partida_id:
            prox.visitante_id = venc if prox.origem_visitante_tipo == TipoOrigem.VENCEDOR else perd
            mudou = True
        if mudou:
            session.add(prox)
            atualizadas.append(prox)

    if atualizadas:
        session.commit()
    return atualizadas


def _carregar_mapeamento() -> dict[str, dict[str, str]]:
    mapa: dict[str, dict[str, str]] = {}
    with MAPEAMENTO_PATH.open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter=";"):
            mapa[row["combinacao"]] = {v: row[v] for v in VENCEDORES_3O}
    return mapa


def classificacao_real_grupos(session: Session) -> dict[str, list]:
    """Classificação oficial de cada grupo (nome -> linhas ordenadas 1º..4º)."""
    grupos = {g.id: g.nome for g in session.exec(select(Grupo)).all()}
    partidas = match_repo.listar(session, FasePartida.GRUPOS)
    por_grupo: dict[int, list[Partida]] = {}
    for p in partidas:
        por_grupo.setdefault(p.grupo_id, []).append(p)

    out: dict[str, list] = {}
    for gid, nome in grupos.items():
        jogos_g = por_grupo.get(gid, [])
        times = sorted(
            {p.mandante_id for p in jogos_g if p.mandante_id}
            | {p.visitante_id for p in jogos_g if p.visitante_id}
        )
        jogos = [
            (p.mandante_id, p.visitante_id, p.placar_mandante, p.placar_visitante)
            for p in jogos_g
        ]
        out[nome] = standings_service.classificar_grupo(times, jogos)
    return out


def _resolver_slot(slot, slot_mandante_jogo, pos1, pos2, terceiro, combo):
    if not slot:
        return None
    if slot.startswith("3"):  # 3º colocado — enfrenta o vencedor em slot_mandante_jogo
        grupo3 = combo[slot_mandante_jogo]
        return terceiro[grupo3]
    posicao, grupo = slot[0], slot[1]
    return pos1[grupo] if posicao == "1" else pos2[grupo]


def resolver_32avos(session: Session) -> tuple[bool, str]:
    """Preenche as 32avas (1º/2º + 8 melhores 3º) quando a fase de grupos termina."""
    grupos_part = match_repo.listar(session, FasePartida.GRUPOS)
    if not grupos_part or any(
        p.placar_mandante is None or p.status != StatusPartida.FINALIZADO for p in grupos_part
    ):
        return False, "Fase de grupos ainda não finalizada (todos os 72 jogos precisam de placar)."

    classif = classificacao_real_grupos(session)
    pos1 = {n: linhas[0].selecao_id for n, linhas in classif.items()}
    pos2 = {n: linhas[1].selecao_id for n, linhas in classif.items()}
    terceiro = {n: linhas[2].selecao_id for n, linhas in classif.items()}

    # 8 melhores 3º colocados (pontos -> saldo -> gols pró -> id)
    terceiros = [(n, linhas[2]) for n, linhas in classif.items()]
    terceiros.sort(
        key=lambda t: (t[1].pontos, t[1].saldo, t[1].gols_pro, -t[1].selecao_id), reverse=True
    )
    melhores = sorted(n for n, _ in terceiros[:8])
    combo_key = "".join(melhores)

    mapa = _carregar_mapeamento()
    if combo_key not in mapa:
        return False, f"Combinação dos 3º não encontrada na tabela: {combo_key}"
    combo = mapa[combo_key]

    r32 = [p for p in match_repo.listar(session) if p.fase == FasePartida.R32]
    for p in r32:
        p.mandante_id = _resolver_slot(p.slot_mandante, p.slot_mandante, pos1, pos2, terceiro, combo)
        p.visitante_id = _resolver_slot(
            p.slot_visitante, p.slot_mandante, pos1, pos2, terceiro, combo
        )
        session.add(p)
    session.commit()
    return True, f"32avos preenchidas (3º classificados: {', '.join(melhores)})."
