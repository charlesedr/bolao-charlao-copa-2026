import streamlit as st
from sqlmodel import Session

from app.core.db import engine
from app.services import ranking_service
from app.ui import session as sess


def render() -> None:
    sess.current_user()
    st.title("⚔️ Comparar participantes")

    with Session(engine) as s:
        ranking = ranking_service.ranking(s)

    if len(ranking) < 2:
        st.info("Ainda não há participantes suficientes para comparar.")
        return

    apelidos = [r["apelido"] for r in ranking]
    c1, c2 = st.columns(2)
    a = c1.selectbox("Participante A", apelidos, index=0)
    b = c2.selectbox("Participante B", apelidos, index=min(1, len(apelidos) - 1))

    ra = next(r for r in ranking if r["apelido"] == a)
    rb = next(r for r in ranking if r["apelido"] == b)

    c1.metric(f"{a}", ra["pontos"], f"{ra['posicao']}º lugar · {ra['placares_exatos']} placares exatos")
    c2.metric(f"{b}", rb["pontos"], f"{rb['posicao']}º lugar · {rb['placares_exatos']} placares exatos")

    diff = ra["pontos"] - rb["pontos"]
    if diff > 0:
        st.success(f"**{a}** está na frente por {diff} ponto(s).")
    elif diff < 0:
        st.success(f"**{b}** está na frente por {-diff} ponto(s).")
    else:
        st.info("Empate em pontos!")
