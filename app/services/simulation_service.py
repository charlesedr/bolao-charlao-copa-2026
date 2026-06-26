"""Simulação da Copa pelo usuário ("Minha Copa") — derivada dos palpites do usuário."""
from sqlmodel import Session, select

from app.domain.enums import FasePartida, StatusPartida
from app.domain.models import Grupo, Palpite, Partida, Selecao
from app.repositories import match_repo
from app.services import bracket_service, standings_service


def _jogo_grupo_hibrido(
    partida: Partida, palpite: Palpite | None
) -> tuple[standings_service.Jogo | None, str]:
    """Usa placar oficial finalizado; senao, usa o palpite do usuario."""
    if partida.mandante_id is None or partida.visitante_id is None:
        return None, "pendente"

    if (
        partida.status == StatusPartida.FINALIZADO
        and partida.placar_mandante is not None
        and partida.placar_visitante is not None
    ):
        return (
            partida.mandante_id,
            partida.visitante_id,
            partida.placar_mandante,
            partida.placar_visitante,
        ), "oficial"

    if palpite is None:
        return None, "pendente"

    return (
        partida.mandante_id,
        partida.visitante_id,
        palpite.gols_mandante,
        palpite.gols_visitante,
    ), "palpite"


def simular_grupos(session: Session, usuario_id: int) -> tuple[dict, dict[int, Selecao]]:
    """Calcula a classificação de cada grupo a partir dos palpites do usuário.

    Um grupo só é simulado se o usuário palpitou em TODAS as suas 6 partidas.
    Retorna ({nome_grupo: info}, mapa_selecoes).
    """
    grupos = {g.id: g.nome for g in session.exec(select(Grupo)).all()}
    selecoes = {s.id: s for s in session.exec(select(Selecao)).all()}
    partidas = session.exec(
        select(Partida).where(Partida.fase == FasePartida.GRUPOS)
    ).all()
    palpites = {
        p.partida_id: p
        for p in session.exec(select(Palpite).where(Palpite.usuario_id == usuario_id)).all()
    }

    por_grupo: dict[int, list[Partida]] = {}
    for p in partidas:
        por_grupo.setdefault(p.grupo_id, []).append(p)

    resultado: dict[str, dict] = {}
    for gid, nome in sorted(grupos.items(), key=lambda x: x[1]):
        jogos_grupo = por_grupo.get(gid, [])
        times = sorted(
            {p.mandante_id for p in jogos_grupo if p.mandante_id}
            | {p.visitante_id for p in jogos_grupo if p.visitante_id}
        )
        palpitados = [p for p in jogos_grupo if p.id in palpites]
        completo = len(jogos_grupo) > 0 and len(palpitados) == len(jogos_grupo)

        linhas = None
        if completo:
            jogos = [
                (
                    p.mandante_id,
                    p.visitante_id,
                    palpites[p.id].gols_mandante,
                    palpites[p.id].gols_visitante,
                )
                for p in jogos_grupo
            ]
            linhas = standings_service.classificar_grupo(times, jogos)

        resultado[nome] = {
            "completo": completo,
            "linhas": linhas,
            "total_jogos": len(jogos_grupo),
            "palpitados": len(palpitados),
        }
    return resultado, selecoes


def simular_grupos_hibrido(session: Session, usuario_id: int) -> tuple[dict, dict[int, Selecao]]:
    """Classifica grupos com jogos oficiais + palpites nos jogos ainda nao finalizados."""
    grupos = {g.id: g.nome for g in session.exec(select(Grupo)).all()}
    selecoes = {s.id: s for s in session.exec(select(Selecao)).all()}
    partidas = session.exec(
        select(Partida).where(Partida.fase == FasePartida.GRUPOS)
    ).all()
    palpites = {
        p.partida_id: p
        for p in session.exec(select(Palpite).where(Palpite.usuario_id == usuario_id)).all()
    }

    por_grupo: dict[int, list[Partida]] = {}
    for p in partidas:
        por_grupo.setdefault(p.grupo_id, []).append(p)

    resultado: dict[str, dict] = {}
    for gid, nome in sorted(grupos.items(), key=lambda x: x[1]):
        jogos_grupo = por_grupo.get(gid, [])
        times = sorted(
            {p.mandante_id for p in jogos_grupo if p.mandante_id}
            | {p.visitante_id for p in jogos_grupo if p.visitante_id}
        )

        jogos: list[standings_service.Jogo] = []
        oficiais = 0
        projetados = 0
        pendentes = 0
        for p in jogos_grupo:
            jogo, origem = _jogo_grupo_hibrido(p, palpites.get(p.id))
            if jogo is None:
                pendentes += 1
                continue
            jogos.append(jogo)
            if origem == "oficial":
                oficiais += 1
            else:
                projetados += 1

        completo = len(jogos_grupo) > 0 and pendentes == 0 and len(jogos) == len(jogos_grupo)
        resultado[nome] = {
            "completo": completo,
            "linhas": standings_service.classificar_grupo(times, jogos) if completo else None,
            "total_jogos": len(jogos_grupo),
            "oficiais": oficiais,
            "projetados": projetados,
            "pendentes": pendentes,
        }
    return resultado, selecoes


def simular_mata_mata(
    session: Session, usuario_id: int
) -> tuple[list[dict] | None, str]:
    """Prévia das 32avas a partir das previsões do usuário nos grupos.

    Retorna (lista de pares {codigo, mandante, visitante, mandante_id, visitante_id}, msg)
    ou (None, motivo) se faltar palpite em algum grupo.
    """
    grupos, selecoes = simular_grupos_hibrido(session, usuario_id)
    if not all(info["completo"] for info in grupos.values()):
        return None, (
            "Complete os palpites dos jogos de grupo que ainda nao tem resultado "
            "oficial para simular o mata-mata."
        )

    pos1 = {n: info["linhas"][0].selecao_id for n, info in grupos.items()}
    pos2 = {n: info["linhas"][1].selecao_id for n, info in grupos.items()}
    terceiro = {n: info["linhas"][2].selecao_id for n, info in grupos.items()}

    terceiros = [(n, info["linhas"][2]) for n, info in grupos.items()]
    terceiros.sort(
        key=lambda t: (t[1].pontos, t[1].saldo, t[1].gols_pro, -t[1].selecao_id), reverse=True
    )
    melhores = sorted(n for n, _ in terceiros[:8])
    combo_key = "".join(melhores)

    mapa = bracket_service._carregar_mapeamento()
    if combo_key not in mapa:
        return None, f"Combinação dos 3º não encontrada: {combo_key}"
    combo = mapa[combo_key]

    r32 = sorted(
        (p for p in match_repo.listar(session) if p.fase == FasePartida.R32),
        key=lambda p: int(p.codigo),
    )
    pares = []
    for p in r32:
        mid = bracket_service._resolver_slot(
            p.slot_mandante, p.slot_mandante, pos1, pos2, terceiro, combo
        )
        vid = bracket_service._resolver_slot(
            p.slot_visitante, p.slot_mandante, pos1, pos2, terceiro, combo
        )
        pares.append(
            {
                "codigo": p.codigo,
                "mandante": selecoes[mid].nome_pt if mid in selecoes else "?",
                "visitante": selecoes[vid].nome_pt if vid in selecoes else "?",
            }
        )
    return pares, f"Previa com resultados oficiais + seus palpites (3os: {', '.join(melhores)})."
