from app.core.timezone import format_brt, now_utc
from app.domain.enums import FasePartida, StatusPartida
from app.domain.models import Partida, Selecao

FASE_LABEL = {
    FasePartida.GRUPOS: "Fase de grupos",
    FasePartida.R32: "32avos",
    FasePartida.OITAVAS: "Oitavas",
    FasePartida.QUARTAS: "Quartas",
    FasePartida.SEMIFINAL: "Semifinal",
    FasePartida.DISPUTA_3O: "Disputa de 3º",
    FasePartida.FINAL: "Final",
}


def nome_time(selecoes: dict[int, Selecao], sid: int | None, slot: str | None) -> str:
    if sid and sid in selecoes:
        return selecoes[sid].nome_pt
    return f"({slot})" if slot else "A definir"


def label_partida(partida: Partida, selecoes: dict[int, Selecao]) -> str:
    m = nome_time(selecoes, partida.mandante_id, partida.slot_mandante)
    v = nome_time(selecoes, partida.visitante_id, partida.slot_visitante)
    quando = format_brt(partida.data_hora, "%d/%m %H:%M")
    return f"{m} x {v} · {quando}"


def indice_partida_default(
    partidas: list[Partida], prefer_em_andamento: bool = True
) -> int:
    """Sugere o índice da partida 'mais importante agora' numa lista ordenada por data_hora.

    Ordem de preferência:
      1) se ``prefer_em_andamento`` → primeira com status EM_ANDAMENTO;
      2) primeira ainda futura (data_hora >= agora);
      3) última partida (já passou tudo, fallback).
    """
    if prefer_em_andamento:
        for i, p in enumerate(partidas):
            if p.status == StatusPartida.EM_ANDAMENTO:
                return i
    agora = now_utc()
    for i, p in enumerate(partidas):
        if p.data_hora >= agora:
            return i
    return max(0, len(partidas) - 1)


def badge_status(partida: Partida) -> str:
    if partida.status == StatusPartida.FINALIZADO:
        return "✅ Finalizado"
    if partida.status == StatusPartida.EM_ANDAMENTO:
        return "🔴 Em andamento"
    return "🟢 Não iniciado"
