"""Roda a sincronização ESPN → banco. Usado por GitHub Actions e localmente.

Uso:
    python scripts/sync_results.py                    # sync padrão
    python scripts/sync_results.py --dry-run          # só conta o que faria
    python scripts/sync_results.py --dias-atras 3     # janela maior
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlmodel import Session  # noqa: E402

from app.core.db import engine  # noqa: E402
from app.services import results_sync_service  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--dias-atras", type=int, default=1)
    parser.add_argument("--dias-a-frente", type=int, default=1)
    args = parser.parse_args()

    with Session(engine) as s:
        stats = results_sync_service.sincronizar(
            s,
            dias_atras=args.dias_atras,
            dias_a_frente=args.dias_a_frente,
            dry_run=args.dry_run,
        )
    print(json.dumps(stats, indent=2, ensure_ascii=False, default=str))
    return 0 if not stats.get("erros") else 0  # erros parciais não falham o job


if __name__ == "__main__":
    sys.exit(main())
