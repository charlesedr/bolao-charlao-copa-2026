"""Popula as 104 partidas (72 grupos + 32 mata-mata) a partir dos CSVs."""
from sqlmodel import Session, select

from _common import brt_para_utc, ler_csv  # noqa: E402

from app.core.db import engine
from app.domain.enums import FasePartida
from app.domain.models import Grupo, Partida, Selecao


def main() -> None:
    grupos_csv = ler_csv("partidas_fase_grupos.csv")
    mata_csv = ler_csv("partidas_mata_mata.csv")

    with Session(engine) as session:
        if session.exec(select(Partida)).first():
            print("Partidas já populadas — nada a fazer.")
            return

        selecao_por_codigo = {
            s.codigo_fifa: s.id for s in session.exec(select(Selecao)).all()
        }
        grupo_por_nome = {g.nome: g.id for g in session.exec(select(Grupo)).all()}
        if not selecao_por_codigo:
            print("ERRO: rode seed_selecoes_grupos.py primeiro.")
            return

        id_por_codigo: dict[str, int] = {}

        # --- Fase de grupos ---
        for lin in grupos_csv:
            p = Partida(
                codigo=lin["codigo"],
                fase=FasePartida.GRUPOS,
                grupo_id=grupo_por_nome[lin["grupo"]],
                mandante_id=selecao_por_codigo[lin["mandante"]],
                visitante_id=selecao_por_codigo[lin["visitante"]],
                data_hora=brt_para_utc(lin["data_brasilia"], lin["hora_brasilia"]),
                estadio=lin["estadio"],
                cidade=lin["cidade"],
            )
            session.add(p)
            session.flush()
            id_por_codigo[lin["codigo"]] = p.id

        # --- Mata-mata (ordem do arquivo: 73->104, origem sempre aponta para jogo anterior) ---
        for lin in mata_csv:
            om = lin.get("origem_mandante") or None
            ov = lin.get("origem_visitante") or None
            p = Partida(
                codigo=lin["codigo"],
                fase=lin["fase"],
                data_hora=brt_para_utc(lin["data_brasilia"], lin["hora_brasilia"]),
                slot_mandante=lin["slot_mandante"],
                slot_visitante=lin["slot_visitante"],
                origem_mandante_id=id_por_codigo[om] if om else None,
                origem_mandante_tipo=lin.get("tipo_mandante") or None,
                origem_visitante_id=id_por_codigo[ov] if ov else None,
                origem_visitante_tipo=lin.get("tipo_visitante") or None,
                estadio=lin["estadio"],
                cidade=lin["cidade"],
            )
            session.add(p)
            session.flush()
            id_por_codigo[lin["codigo"]] = p.id

        session.commit()
        print(f"OK: {len(grupos_csv)} jogos de grupos + {len(mata_csv)} de mata-mata inseridos.")


if __name__ == "__main__":
    main()
