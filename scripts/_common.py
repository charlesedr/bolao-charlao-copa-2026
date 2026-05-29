"""Utilidades compartilhadas pelos scripts de seed."""
import csv
import sys
from datetime import UTC, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

# Garante que o pacote app seja importável quando rodado como script direto.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
BRT = ZoneInfo("America/Sao_Paulo")


def ler_csv(nome: str) -> list[dict[str, str]]:
    caminho = DATA_DIR / nome
    with caminho.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def brt_para_utc(data_ddmmaaaa: str, hora_hhmm: str) -> datetime:
    """Converte data/hora de Brasília (dd/mm/aaaa hh:mm) para datetime UTC tz-aware."""
    dt_local = datetime.strptime(f"{data_ddmmaaaa} {hora_hhmm}", "%d/%m/%Y %H:%M")
    return dt_local.replace(tzinfo=BRT).astimezone(UTC)
