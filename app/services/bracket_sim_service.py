"""Bracket simulado em Minha Copa — cascata sobre as partidas do mata-mata.

Não vale ponto no bolão. Os palpites reais (que pontuam) ficam em ``Palpite``
e dependem dos times oficiais. Este serviço usa resultados oficiais dos grupos
e os palpites restantes para determinar os times das 32avas e, em cima disso, deixa o
usuário escolher vencedor + placar de cada confronto. O vencedor vira
mandante/visitante do confronto seguinte (cascata).
"""
from sqlmodel import Session, select

from app.domain.enums import FasePartida, TipoOrigem
from app.domain.models import PalpiteBracketSimulado, Partida
from app.repositories import match_repo
from app.services import bracket_service, simulation_service

FASES_ORDEM = [
    FasePartida.R32,
    FasePartida.OITAVAS,
    FasePartida.QUARTAS,
    FasePartida.SEMIFINAL,
    FasePartida.FINAL,
    FasePartida.DISPUTA_3O,
]


def _palpites_por_partida(session: Session, usuario_id: int) -> dict[int, PalpiteBracketSimulado]:
    return {
        p.partida_id: p
        for p in session.exec(
            select(PalpiteBracketSimulado).where(
                PalpiteBracketSimulado.usuario_id == usuario_id
            )
        ).all()
    }


def _resolver_r32(session: Session, usuario_id: int) -> tuple[dict[int, tuple[int, int]] | None, str]:
    """Para cada partida das 32avas, retorna (mandante_id, visitante_id) a partir
    da classificacao hibrida dos grupos. Retorna None se grupos incompletos."""
    grupos, _ = simulation_service.simular_grupos_hibrido(session, usuario_id)
    if not all(info["completo"] for info in grupos.values()):
        return None, (
            "Falta palpite em jogo de grupo que ainda nao tem resultado oficial. "
            "Complete esses palpites para liberar o mata-mata aqui."
        )

    pos1 = {n: info["linhas"][0].selecao_id for n, info in grupos.items()}
    pos2 = {n: info["linhas"][1].selecao_id for n, info in grupos.items()}
    terceiro = {n: info["linhas"][2].selecao_id for n, info in grupos.items()}

    terceiros = [(n, info["linhas"][2]) for n, info in grupos.items()]
    terceiros.sort(
        key=lambda t: (t[1].pontos, t[1].saldo, t[1].gols_pro, -t[1].selecao_id),
        reverse=True,
    )
    melhores = sorted(n for n, _ in terceiros[:8])
    combo_key = "".join(melhores)

    mapa = bracket_service._carregar_mapeamento()
    if combo_key not in mapa:
        return None, f"Combinação dos 3º colocados não encontrada: {combo_key}"
    combo = mapa[combo_key]

    r32 = [p for p in match_repo.listar(session) if p.fase == FasePartida.R32]
    out: dict[int, tuple[int, int]] = {}
    for p in r32:
        mid = bracket_service._resolver_slot(
            p.slot_mandante, p.slot_mandante, pos1, pos2, terceiro, combo
        )
        vid = bracket_service._resolver_slot(
            p.slot_visitante, p.slot_mandante, pos1, pos2, terceiro, combo
        )
        if mid is not None and vid is not None:
            out[p.id] = (mid, vid)
    return out, ""


def _vencedor_perdedor_sim(
    palpite: PalpiteBracketSimulado, mandante_id: int, visitante_id: int
) -> tuple[int, int] | tuple[None, None]:
    """Dado o palpite simulado + os times do confronto, retorna (vencedor, perdedor)."""
    if palpite.vencedor_id == mandante_id:
        return mandante_id, visitante_id
    if palpite.vencedor_id == visitante_id:
        return visitante_id, mandante_id
    # vencedor não está no confronto (cascata quebrada)
    return None, None


def montar_chave(session: Session, usuario_id: int) -> dict:
    """Constrói o bracket simulado completo.

    Retorna ``{
        "status": "ok" | "incompleto",
        "msg": str,
        "fases": {fase: [{"partida_id", "codigo", "mandante_id", "visitante_id",
                          "palpite": PalpiteBracketSimulado | None,
                          "dependencia_pendente": bool}]},
        "campeao_id": int | None,
        "inconsistencias": [str],
    }``"""
    r32_times, msg = _resolver_r32(session, usuario_id)
    if r32_times is None:
        return {"status": "incompleto", "msg": msg, "fases": {}, "campeao_id": None,
                "inconsistencias": []}

    palpites = _palpites_por_partida(session, usuario_id)
    partidas = {
        p.id: p
        for p in match_repo.listar(session)
        if p.fase in FASES_ORDEM
    }

    # times resolvidos por confronto (id -> (mandante, visitante))
    times_por_partida: dict[int, tuple[int | None, int | None]] = {}
    for pid, (m, v) in r32_times.items():
        times_por_partida[pid] = (m, v)

    inconsistencias: list[str] = []
    fases_out: dict[str, list[dict]] = {}

    for fase in FASES_ORDEM:
        confrontos = sorted(
            (p for p in partidas.values() if p.fase == fase),
            key=lambda x: int(x.codigo),
        )
        items: list[dict] = []
        for p in confrontos:
            mandante_id, visitante_id = times_por_partida.get(p.id, (None, None))

            # Para fases após R32: resolve mandante/visitante pelo vencedor/perdedor
            # do palpite simulado da partida-origem.
            if fase != FasePartida.R32:
                if p.origem_mandante_id is not None and mandante_id is None:
                    origem_pal = palpites.get(p.origem_mandante_id)
                    origem_times = times_por_partida.get(
                        p.origem_mandante_id, (None, None)
                    )
                    if origem_pal and all(origem_times):
                        venc, perd = _vencedor_perdedor_sim(
                            origem_pal, origem_times[0], origem_times[1]
                        )
                        if venc is not None:
                            mandante_id = (
                                venc if p.origem_mandante_tipo == TipoOrigem.VENCEDOR else perd
                            )
                if p.origem_visitante_id is not None and visitante_id is None:
                    origem_pal = palpites.get(p.origem_visitante_id)
                    origem_times = times_por_partida.get(
                        p.origem_visitante_id, (None, None)
                    )
                    if origem_pal and all(origem_times):
                        venc, perd = _vencedor_perdedor_sim(
                            origem_pal, origem_times[0], origem_times[1]
                        )
                        if venc is not None:
                            visitante_id = (
                                venc if p.origem_visitante_tipo == TipoOrigem.VENCEDOR else perd
                            )
                times_por_partida[p.id] = (mandante_id, visitante_id)

            dependencia_pendente = mandante_id is None or visitante_id is None

            palpite = palpites.get(p.id)
            # Detecta inconsistência: palpite tem vencedor que não está mais
            # nos times atuais do confronto.
            if (
                palpite is not None
                and not dependencia_pendente
                and palpite.vencedor_id not in (mandante_id, visitante_id)
            ):
                inconsistencias.append(
                    f"{_label_fase(fase)} jogo #{p.codigo}: vencedor simulado "
                    f"não joga mais este confronto."
                )

            items.append(
                {
                    "partida_id": p.id,
                    "codigo": p.codigo,
                    "mandante_id": mandante_id,
                    "visitante_id": visitante_id,
                    "palpite": palpite,
                    "dependencia_pendente": dependencia_pendente,
                }
            )
        fases_out[fase] = items

    # campeão = vencedor da final
    campeao_id: int | None = None
    finais = fases_out.get(FasePartida.FINAL, [])
    if finais:
        f0 = finais[0]
        pal = f0["palpite"]
        if pal and not f0["dependencia_pendente"]:
            campeao_id = pal.vencedor_id

    return {
        "status": "ok",
        "msg": "",
        "fases": fases_out,
        "campeao_id": campeao_id,
        "inconsistencias": inconsistencias,
    }


def fase_completa(items: list[dict]) -> bool:
    """True se todos os confrontos da fase têm palpite (sem dependência pendente)."""
    if not items:
        return False
    return all(
        (not it["dependencia_pendente"]) and it["palpite"] is not None for it in items
    )


def salvar(
    session: Session,
    *,
    usuario_id: int,
    partida_id: int,
    vencedor_id: int,
    placar_vencedor: int,
    placar_perdedor: int,
) -> tuple[bool, str]:
    """Cria ou atualiza um palpite simulado. Valida placar e vencedor."""
    if placar_vencedor < placar_perdedor:
        return False, "Placar do vencedor deve ser ≥ placar do perdedor."
    if placar_vencedor < 0 or placar_perdedor < 0 or placar_vencedor > 30 or placar_perdedor > 30:
        return False, "Placar fora do intervalo (0 a 30)."

    partida = session.get(Partida, partida_id)
    if partida is None:
        return False, "Partida não encontrada."

    existente = session.exec(
        select(PalpiteBracketSimulado).where(
            PalpiteBracketSimulado.usuario_id == usuario_id,
            PalpiteBracketSimulado.partida_id == partida_id,
        )
    ).first()
    if existente is None:
        existente = PalpiteBracketSimulado(
            usuario_id=usuario_id,
            partida_id=partida_id,
            vencedor_id=vencedor_id,
            placar_vencedor=placar_vencedor,
            placar_perdedor=placar_perdedor,
        )
        session.add(existente)
    else:
        existente.vencedor_id = vencedor_id
        existente.placar_vencedor = placar_vencedor
        existente.placar_perdedor = placar_perdedor
        session.add(existente)
    session.commit()
    return True, "Palpite simulado salvo."


def resetar(session: Session, usuario_id: int) -> int:
    """Apaga todos os palpites simulados do usuário. Retorna a quantidade removida."""
    pals = session.exec(
        select(PalpiteBracketSimulado).where(
            PalpiteBracketSimulado.usuario_id == usuario_id
        )
    ).all()
    n = len(pals)
    for p in pals:
        session.delete(p)
    session.commit()
    return n


def _label_fase(fase: str) -> str:
    return {
        FasePartida.R32: "32avos",
        FasePartida.OITAVAS: "Oitavas",
        FasePartida.QUARTAS: "Quartas",
        FasePartida.SEMIFINAL: "Semifinal",
        FasePartida.FINAL: "Final",
        FasePartida.DISPUTA_3O: "Disputa de 3º",
    }.get(fase, fase)
