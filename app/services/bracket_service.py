"""Avanço automático do mata-mata: propaga vencedor/perdedor para os próximos jogos."""
from sqlmodel import Session, select

from app.domain.enums import FasePartida, TipoOrigem
from app.domain.models import Partida
from app.repositories import match_repo


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
