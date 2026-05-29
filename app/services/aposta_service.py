"""Aposta na classificação final (campeão/vice/3º/4º): trava, salvamento e pontuação."""
from datetime import timedelta

from sqlmodel import Session, select

from app.core.timezone import now_utc
from app.domain.enums import FasePartida
from app.domain.models import ApostaClassificacaoFinal, Partida
from app.services import bracket_service, scoring_service

LIMITE_MINUTOS = 5


def _partida_disputa3(session: Session) -> Partida | None:
    return session.exec(
        select(Partida).where(Partida.fase == FasePartida.DISPUTA_3O)
    ).first()


def aposta_aberta(session: Session) -> bool:
    """Aberta até 5 min antes do jogo de disputa do 3º lugar (Final de Bronze)."""
    partida = _partida_disputa3(session)
    if partida is None:
        return True
    return now_utc() < partida.data_hora - timedelta(minutes=LIMITE_MINUTOS)


def get_aposta(session: Session, usuario_id: int) -> ApostaClassificacaoFinal | None:
    return session.exec(
        select(ApostaClassificacaoFinal).where(
            ApostaClassificacaoFinal.usuario_id == usuario_id
        )
    ).first()


def salvar_aposta(
    session: Session,
    *,
    usuario_id: int,
    campeao_id: int,
    vice_id: int,
    terceiro_id: int,
    quarto_id: int,
) -> tuple[bool, str]:
    if not aposta_aberta(session):
        return False, "As apostas estão encerradas."
    ids = [campeao_id, vice_id, terceiro_id, quarto_id]
    if any(x is None for x in ids):
        return False, "Escolha as 4 seleções."
    if len(set(ids)) != 4:
        return False, "As 4 seleções devem ser diferentes."

    aposta = get_aposta(session, usuario_id)
    if aposta is None:
        aposta = ApostaClassificacaoFinal(usuario_id=usuario_id)
        session.add(aposta)
    aposta.campeao_id = campeao_id
    aposta.vice_id = vice_id
    aposta.terceiro_id = terceiro_id
    aposta.quarto_id = quarto_id
    session.commit()
    return True, "Aposta salva!"


def posicoes_oficiais(session: Session) -> dict[str, int | None]:
    """Campeão/vice = vencedor/perdedor da final; 3º/4º = vencedor/perdedor da disputa de 3º."""
    final = session.exec(select(Partida).where(Partida.fase == FasePartida.FINAL)).first()
    bronze = _partida_disputa3(session)
    campeao, vice = bracket_service.vencedor_perdedor(final) if final else (None, None)
    terceiro, quarto = bracket_service.vencedor_perdedor(bronze) if bronze else (None, None)
    return {"campeao": campeao, "vice": vice, "terceiro": terceiro, "quarto": quarto}


def calcular_apostas(session: Session) -> None:
    """Recalcula a pontuação de todas as apostas a partir das posições oficiais."""
    pos = posicoes_oficiais(session)
    for aposta in session.exec(select(ApostaClassificacaoFinal)).all():
        scoring_service.calcular_pontos_aposta_final(
            aposta,
            campeao_id=pos["campeao"],
            vice_id=pos["vice"],
            terceiro_id=pos["terceiro"],
            quarto_id=pos["quarto"],
        )
        session.add(aposta)
    session.commit()
