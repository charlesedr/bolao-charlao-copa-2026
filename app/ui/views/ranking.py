import pandas as pd
import streamlit as st
from sqlmodel import Session

from app.core.db import engine
from app.services import ranking_service


@st.cache_data(ttl=10)
def _ranking_cache() -> list[dict]:
    with Session(engine) as s:
        return ranking_service.ranking(s)


def render() -> None:
    st.title("🏆 Ranking geral")
    linhas = _ranking_cache()
    if not linhas:
        st.info("Ainda não há participantes aprovados ou pontuações.")
        return

    df = pd.DataFrame(linhas)
    df["nome"] = df["nome"].fillna("").str.strip()
    df = df[["posicao", "nome", "apelido", "pontos", "placares_exatos", "resultados", "gols"]]
    df.columns = ["#", "Nome", "Apelido", "Pontos", "Placares", "Resultados", "Gols"]
    st.dataframe(df, hide_index=True, use_container_width=True)
    st.caption(
        "Atualizado após o final de cada partida. Desempate: pontos → placares exatos → "
        "resultados acertados → gols acertados (empate total = mesma posição)."
    )
