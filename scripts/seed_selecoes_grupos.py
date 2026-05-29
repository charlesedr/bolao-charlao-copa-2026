"""Popula grupos (A-L) e as 48 seleções a partir de data/selecoes.csv."""
from sqlmodel import Session, select

from _common import ler_csv  # noqa: E402  (ajuste de sys.path em _common)

from app.core.db import engine
from app.domain.models import Grupo, Selecao


def main() -> None:
    linhas = ler_csv("selecoes.csv")
    with Session(engine) as session:
        if session.exec(select(Selecao)).first():
            print("Seleções já populadas — nada a fazer.")
            return

        # Grupos
        nomes_grupos = sorted({lin["grupo"] for lin in linhas})
        grupo_por_nome: dict[str, Grupo] = {}
        for nome in nomes_grupos:
            g = Grupo(nome=nome)
            session.add(g)
            grupo_por_nome[nome] = g
        session.flush()

        # Seleções
        for lin in linhas:
            session.add(
                Selecao(
                    codigo_fifa=lin["codigo_fifa"],
                    nome=lin["nome"],
                    nome_pt=lin["nome_pt"],
                    grupo_id=grupo_por_nome[lin["grupo"]].id,
                    confederacao=lin.get("confederacao") or None,
                )
            )
        session.commit()
        print(f"OK: {len(nomes_grupos)} grupos e {len(linhas)} seleções inseridos.")


if __name__ == "__main__":
    main()
