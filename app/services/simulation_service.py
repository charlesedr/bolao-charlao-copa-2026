"""Simulação da Copa pelo usuário ("Minha Copa") — derivada dos palpites do usuário."""
from sqlmodel import Session, select

from app.domain.enums import FasePartida
from app.domain.models import Grupo, Palpite, Partida, Selecao
from app.services import standings_service


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
