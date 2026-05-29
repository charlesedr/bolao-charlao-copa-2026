"""Palpites: trava de 5 minutos, validação e UPSERT."""
from datetime import timedelta

from sqlmodel import Session

from app.core.timezone import now_utc
from app.domain.enums import FasePartida
from app.domain.models import Palpite, Partida
from app.repositories import bet_repo, match_repo

LIMITE_MINUTOS = 5


def prazo_limite(partida: Partida):
    return partida.data_hora - timedelta(minutes=LIMITE_MINUTOS)


def palpite_aberto(partida: Partida) -> bool:
    """Aberto se os times já estão definidos e faltam mais de 5 min para o início."""
    if partida.mandante_id is None or partida.visitante_id is None:
        return False
    return now_utc() < prazo_limite(partida)


def salvar_palpite(
    session: Session,
    *,
    usuario_id: int,
    partida_id: int,
    gols_mandante: int,
    gols_visitante: int,
    classificado_id: int | None = None,
) -> tuple[bool, str]:
    partida = match_repo.get(session, partida_id)
    if partida is None:
        return False, "Partida não encontrada."
    if not palpite_aberto(partida):
        return False, "Palpite encerrado para esta partida."
    if not (0 <= gols_mandante <= 30 and 0 <= gols_visitante <= 30):
        return False, "Placar inválido (0 a 30)."

    is_mata_mata = partida.fase != FasePartida.GRUPOS
    if is_mata_mata:
        if gols_mandante == gols_visitante:
            if classificado_id not in (partida.mandante_id, partida.visitante_id):
                return False, "Empate: escolha quem se classifica."
        else:
            classificado_id = (
                partida.mandante_id if gols_mandante > gols_visitante else partida.visitante_id
            )
    else:
        classificado_id = None

    palpite = bet_repo.get(session, usuario_id, partida_id)
    if palpite is None:
        palpite = Palpite(
            usuario_id=usuario_id,
            partida_id=partida_id,
            gols_mandante=gols_mandante,
            gols_visitante=gols_visitante,
            classificado_id=classificado_id,
        )
        session.add(palpite)
    else:
        palpite.gols_mandante = gols_mandante
        palpite.gols_visitante = gols_visitante
        palpite.classificado_id = classificado_id
        session.add(palpite)
    session.commit()
    return True, "Palpite salvo!"
