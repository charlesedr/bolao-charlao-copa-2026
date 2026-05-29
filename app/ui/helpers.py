from app.core.timezone import format_brt
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


def badge_status(partida: Partida) -> str:
    if partida.status == StatusPartida.FINALIZADO:
        return "✅ Finalizado"
    if partida.status == StatusPartida.EM_ANDAMENTO:
        return "🔴 Em andamento"
    return "🟢 Não iniciado"
