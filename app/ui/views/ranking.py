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

    df = pd.DataFrame(linhas)[["posicao", "apelido", "pontos", "placares_exatos"]]
    df.columns = ["#", "Apelido", "Pontos", "Placares exatos"]
    st.dataframe(df, hide_index=True, use_container_width=True)
    st.caption("Atualiza a cada 10s. Desempate: pontos → placares exatos → apelido.")
