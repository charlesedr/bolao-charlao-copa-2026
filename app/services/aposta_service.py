"""Aposta na classificação final (campeão/vice/3º/4º): trava, salvamento e pontuação."""
from datetime import timedelta

from sqlmodel import Session, select

from app.core.timezone import now_utc
from app.domain.enums import FasePartida, StatusUsuario
from app.domain.models import ApostaClassificacaoFinal, Partida, Selecao, Usuario
from app.services import bracket_service, scoring_service

LIMITE_MINUTOS = 5


def _primeiro_jogo_copa(session: Session) -> Partida | None:
    """Primeiro jogo cronológico da Copa (jogo 1 da fase de grupos)."""
    return session.exec(
        select(Partida)
        .where(Partida.fase == FasePartida.GRUPOS)
        .order_by(Partida.data_hora)
    ).first()


def _partida_disputa3(session: Session) -> Partida | None:
    """Jogo de disputa do 3º lugar (usado para apurar 3º/4º depois do jogo)."""
    return session.exec(
        select(Partida).where(Partida.fase == FasePartida.DISPUTA_3O)
    ).first()


def aposta_aberta(session: Session) -> bool:
    """Aberta até 5 min antes do PRIMEIRO jogo da Copa (jogo 1, fase de grupos)."""
    partida = _primeiro_jogo_copa(session)
    if partida is None:
        return True
    return now_utc() < partida.data_hora - timedelta(minutes=LIMITE_MINUTOS)


def listar_apostas_completas(session: Session) -> list[dict]:
    """Lista todas as apostas com os 4 campos preenchidos + dados do usuário e nomes
    das seleções, ordenada por pontos desc → apelido. Usada para revelar as apostas
    de todos depois da trava (similar ao reveal de palpites na Tela da Partida)."""
    apostas = session.exec(select(ApostaClassificacaoFinal)).all()
    apostas = [
        a for a in apostas
        if a.campeao_id and a.vice_id and a.terceiro_id and a.quarto_id
    ]
    if not apostas:
        return []

    user_ids = {a.usuario_id for a in apostas}
    usuarios = {
        u.id: u
        for u in session.exec(select(Usuario).where(Usuario.id.in_(user_ids))).all()
    }
    sel_ids: set[int] = set()
    for a in apostas:
        sel_ids.update([a.campeao_id, a.vice_id, a.terceiro_id, a.quarto_id])
    selecoes = {
        s.id: s.nome_pt
        for s in session.exec(select(Selecao).where(Selecao.id.in_(sel_ids))).all()
    }

    linhas = []
    for a in apostas:
        u = usuarios.get(a.usuario_id)
        if u is None:
            continue
        linhas.append({
            "apelido": u.apelido,
            "nome": (u.nome or "").strip(),
            "campeao": selecoes.get(a.campeao_id, "—"),
            "vice": selecoes.get(a.vice_id, "—"),
            "terceiro": selecoes.get(a.terceiro_id, "—"),
            "quarto": selecoes.get(a.quarto_id, "—"),
            "pontos": a.pontos_total or 0,
        })
    linhas.sort(key=lambda x: (-x["pontos"], x["apelido"].lower()))
    return linhas


def contar_apostas(session: Session) -> tuple[int, int]:
    """Retorna ``(apostas_completas, usuarios_aprovados)`` para feedback social."""
    apostas = session.exec(select(ApostaClassificacaoFinal)).all()
    completas = sum(
        1 for a in apostas
        if a.campeao_id and a.vice_id and a.terceiro_id and a.quarto_id
    )
    aprovados = len(
        session.exec(select(Usuario).where(Usuario.status == StatusUsuario.APROVADO)).all()
    )
    return completas, aprovados


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
