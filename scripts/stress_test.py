"""Stress test do banco de dados (DEV).

Sub-comandos
------------
    populate --users N         cria N usuários fake aprovados (apelido 'stress_NNNN')
    run --concurrent N --ops K roda N workers concorrentes, cada um faz K operações
    cleanup                    remove os usuários fake e os dados relacionados

Mix de operações por worker:
    60% leitura do ranking
    30% leitura da lista de partidas
    10% salvar/atualizar palpite

Trava em ENV=prod por segurança.
"""
import argparse
import random
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import create_engine  # noqa: E402
from sqlmodel import Session, delete, select  # noqa: E402

from app.core.config import settings  # noqa: E402
from app.core.security import hash_senha  # noqa: E402
from app.domain.enums import StatusUsuario  # noqa: E402
from app.domain.models import (  # noqa: E402
    ApostaClassificacaoFinal,
    DesempatePalpiteUsuario,
    Palpite,
    Partida,
    PontuacaoPartida,
    Usuario,
)
from app.services import bet_service, ranking_service  # noqa: E402

FAKE_PREFIX = "stress_"


def _stress_engine(pool_size: int = 20, max_overflow: int = 100):
    return create_engine(
        settings.active_database_url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_pre_ping=True,
    )


def _safety() -> None:
    if settings.env == "prod":
        sys.exit("ABORT: stress test não pode rodar em ENV=prod")
    print(f"[OK] ENV={settings.env}")


def cmd_populate(n: int) -> None:
    _safety()
    eng = _stress_engine()
    with Session(eng) as s:
        existentes = s.exec(
            select(Usuario).where(Usuario.apelido.like(f"{FAKE_PREFIX}%"))
        ).all()
        ja = len(existentes)
        print(f"Fakes existentes: {ja}; criando {max(0, n - ja)}...")
        for i in range(ja, n):
            apelido = f"{FAKE_PREFIX}{i:04d}"
            s.add(
                Usuario(
                    nome=f"Stress {i}",
                    apelido=apelido,
                    email=f"{apelido}@stress.test",
                    telefone="00000000000",
                    senha_hash=hash_senha("stress123"),
                    status=StatusUsuario.APROVADO,
                    is_admin=False,
                )
            )
            if (i + 1) % 100 == 0:
                s.commit()
                print(f"  ...{i + 1}")
        s.commit()
    print(f"[OK] {n} fakes aprovados disponíveis.")


def cmd_cleanup() -> None:
    _safety()
    eng = _stress_engine()
    with Session(eng) as s:
        ids = [
            u.id
            for u in s.exec(select(Usuario).where(Usuario.apelido.like(f"{FAKE_PREFIX}%"))).all()
        ]
        if not ids:
            print("Nenhum fake encontrado.")
            return
        print(f"Removendo {len(ids)} fakes e dados...")
        for tab in (Palpite, PontuacaoPartida, ApostaClassificacaoFinal, DesempatePalpiteUsuario):
            s.exec(delete(tab).where(tab.usuario_id.in_(ids)))
        s.exec(delete(Usuario).where(Usuario.id.in_(ids)))
        s.commit()
    print("[OK] cleanup concluído.")


def _op_ranking(eng) -> None:
    with Session(eng) as s:
        ranking_service.ranking(s)


def _op_partidas(eng) -> None:
    with Session(eng) as s:
        s.exec(select(Partida).limit(50)).all()


def _op_palpite(eng, usuario_id: int, partida_id: int) -> None:
    with Session(eng) as s:
        bet_service.salvar_palpite(
            s,
            usuario_id=usuario_id,
            partida_id=partida_id,
            gols_mandante=random.randint(0, 5),
            gols_visitante=random.randint(0, 5),
        )


def _worker(eng, usuario_id: int, partida_ids: list[int], n_ops: int):
    latencias: list[float] = []
    erros = 0
    for _ in range(n_ops):
        op = random.choices(
            ["ranking", "partidas", "palpite"], weights=[60, 30, 10]
        )[0]
        t0 = time.perf_counter()
        try:
            if op == "ranking":
                _op_ranking(eng)
            elif op == "partidas":
                _op_partidas(eng)
            else:
                _op_palpite(eng, usuario_id, random.choice(partida_ids))
        except Exception:
            erros += 1
        else:
            latencias.append((time.perf_counter() - t0) * 1000)
        time.sleep(random.uniform(0.05, 0.15))
    return latencias, erros


def cmd_run(concurrent: int, ops: int) -> None:
    _safety()
    eng = _stress_engine(pool_size=min(50, concurrent), max_overflow=max(50, concurrent * 2))
    with Session(eng) as s:
        partida_ids = [
            p.id for p in s.exec(
                select(Partida).where(Partida.mandante_id.is_not(None)).limit(72)
            ).all()
        ]
        fakes = s.exec(select(Usuario).where(Usuario.apelido.like(f"{FAKE_PREFIX}%"))).all()
    if not partida_ids:
        print("ERRO: sem partidas com times definidos.")
        return
    if not fakes:
        print("ERRO: sem usuários fake. Rode 'populate' primeiro.")
        return

    print("=== Stress test (DEV) ===")
    print(f"  Workers concorrentes: {concurrent}")
    print(f"  Ops por worker:       {ops}")
    print(f"  Total ops alvo:       {concurrent * ops}")
    print(f"  Usuários disponíveis: {len(fakes)} fakes (+ admin/outros)")
    print(f"  Partidas:             {len(partida_ids)}")
    print("  Mix: 60% ranking | 30% partidas | 10% palpite")
    print()

    t0 = time.perf_counter()
    all_lat: list[float] = []
    total_err = 0
    with ThreadPoolExecutor(max_workers=concurrent) as ex:
        futures = [
            ex.submit(_worker, eng, random.choice(fakes).id, partida_ids, ops)
            for _ in range(concurrent)
        ]
        for f in as_completed(futures):
            lats, errs = f.result()
            all_lat.extend(lats)
            total_err += errs
    elapsed = time.perf_counter() - t0

    n = len(all_lat)
    print("=== RESULTADOS ===")
    print(f"  Tempo total:    {elapsed:.2f}s")
    print(f"  Ops sucesso:    {n}")
    print(f"  Erros:          {total_err}")
    if n > 0:
        all_lat.sort()
        avg = statistics.mean(all_lat)
        p50 = all_lat[n // 2]
        p95 = all_lat[min(int(n * 0.95), n - 1)]
        p99 = all_lat[min(int(n * 0.99), n - 1)]
        print(f"  Throughput:     {n / elapsed:.1f} ops/s")
        print(
            f"  Latência (ms):  média={avg:.0f}  p50={p50:.0f}  "
            f"p95={p95:.0f}  p99={p99:.0f}"
        )
        print(f"  Min/Max:        {all_lat[0]:.0f}ms / {all_lat[-1]:.0f}ms")


def main() -> None:
    parser = argparse.ArgumentParser(description="Stress test do banco DEV.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_pop = sub.add_parser("populate")
    p_pop.add_argument("--users", type=int, default=300)
    p_run = sub.add_parser("run")
    p_run.add_argument("--concurrent", type=int, default=50)
    p_run.add_argument("--ops", type=int, default=10)
    sub.add_parser("cleanup")
    args = parser.parse_args()
    if args.cmd == "populate":
        cmd_populate(args.users)
    elif args.cmd == "run":
        cmd_run(args.concurrent, args.ops)
    elif args.cmd == "cleanup":
        cmd_cleanup()


if __name__ == "__main__":
    main()
