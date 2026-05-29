from datetime import UTC, datetime
from zoneinfo import ZoneInfo

BRT = ZoneInfo("America/Sao_Paulo")


def now_utc() -> datetime:
    """Agora, timezone-aware em UTC."""
    return datetime.now(UTC)


def to_brt(dt: datetime) -> datetime:
    """Converte um datetime (UTC ou naive-assumido-UTC) para horário de Brasília."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(BRT)


def format_brt(dt: datetime, fmt: str = "%d/%m %H:%M") -> str:
    """Formata um datetime no horário de Brasília."""
    return to_brt(dt).strftime(fmt)
