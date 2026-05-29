"""Lançamento de placar oficial e recálculo de pontuação."""
from sqlmodel import Session

from app.domain.enums import FasePartida, StatusPartida
from app.repositories import admin_log_repo, bet_repo, match_repo
from app.services import aposta_service, bracket_service, scoring_service


def lancar_placar(
    session: Session,
    *,
    admin_id: int,
    partida_id: int,
    placar_mandante: int,
    placar_visitante: int,
    classificado_id: int | None = None,
    status: str = StatusPartida.FINALIZADO,
) -> tuple[bool, str]:
    partida = match_repo.get(session, partida_id)
    if partida is None:
        return False, "Partida não encontrada."
    if not (0 <= placar_mandante <= 30 and 0 <= placar_visitante <= 30):
        return False, "Placar inválido (0 a 30)."

    is_mata_mata = partida.fase != FasePartida.GRUPOS
    if is_mata_mata and status == StatusPartida.FINALIZADO:
        if placar_mandante == placar_visitante:
            if classificado_id not in (partida.mandante_id, partida.visitante_id):
                return (
                    False,
                    "Mata-mata empatado nos 90 min — informe quem se classificou.",
                )
        else:
            classificado_id = (
                partida.mandante_id
                if placar_mandante > placar_visitante
                else partida.visitante_id
            )

    antes = {
        "placar_mandante": partida.placar_mandante,
        "placar_visitante": partida.placar_visitante,
        "status": partida.status,
    }
    partida.placar_mandante = placar_mandante
    partida.placar_visitante = placar_visitante
    partida.classificado_id = classificado_id if is_mata_mata else None
    partida.status = status
    session.add(partida)
    admin_log_repo.registrar(
        session,
        admin_id=admin_id,
        acao="lancar_placar",
        entidade="partida",
        entidade_id=partida_id,
        detalhes={
            "antes": antes,
            "depois": {
                "placar_mandante": placar_mandante,
                "placar_visitante": placar_visitante,
                "status": str(status),
            },
        },
    )
    session.commit()
    recalcular_partida(session, partida_id)

    # Mata-mata finalizado → propaga vencedor/perdedor para o próximo jogo da chave
    if is_mata_mata and status == StatusPartida.FINALIZADO:
        bracket_service.avancar(session, partida_id)

    # Último jogo da fase de grupos finalizado → preenche as 32avas automaticamente
    if not is_mata_mata and status == StatusPartida.FINALIZADO:
        bracket_service.resolver_32avos(session)

    # Final ou disputa de 3º → recalcula a aposta de classificação final
    if partida.fase in (FasePartida.FINAL, FasePartida.DISPUTA_3O):
        aposta_service.calcular_apostas(session)

    return True, "Resultado salvo e pontuação recalculada."


def definir_status(
    session: Session, *, admin_id: int, partida_id: int, status: str
) -> tuple[bool, str]:
    partida = match_repo.get(session, partida_id)
    if partida is None:
        return False, "Partida não encontrada."
    partida.status = status
    session.add(partida)
    admin_log_repo.registrar(
        session, admin_id=admin_id, acao="alterar_status", entidade="partida",
        entidade_id=partida_id, detalhes={"status": str(status)},
    )
    session.commit()
    return True, "Status atualizado."


def recalcular_partida(session: Session, partida_id: int) -> None:
    partida = match_repo.get(session, partida_id)
    if partida is None or partida.placar_mandante is None:
        return
    for palpite in bet_repo.listar_por_partida(session, partida_id):
        calc = scoring_service.calcular_pontos_palpite(palpite, partida)
        existente = bet_repo.pontuacao(session, palpite.usuario_id, partida_id)
        if existente is None:
            session.add(calc)
        else:
            existente.pontos_gols_mandante = calc.pontos_gols_mandante
            existente.pontos_gols_visitante = calc.pontos_gols_visitante
            existente.pontos_resultado = calc.pontos_resultado
            existente.pontos_placar_exato = calc.pontos_placar_exato
            existente.pontos_classificado = calc.pontos_classificado
            existente.pontos_total = calc.pontos_total
            session.add(existente)
    session.commit()


def recalcular_tudo(session: Session) -> int:
    n = 0
    for partida in match_repo.listar(session):
        if partida.placar_mandante is not None:
            recalcular_partida(session, partida.id)
            n += 1
    return n
