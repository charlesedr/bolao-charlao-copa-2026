import pandas as pd
import streamlit as st
from sqlmodel import Session

from app.core.db import engine
from app.services import simulation_service
from app.ui import session as sess


def _render_grupos(usuario_id: int) -> None:
    st.caption("Classificação simulada a partir dos **seus palpites** da fase de grupos.")
    with Session(engine) as s:
        resultado, selecoes = simulation_service.simular_grupos(s, usuario_id)

    for nome, info in resultado.items():
        st.subheader(f"Grupo {nome}")
        if not info["completo"]:
            st.caption(
                f"⚠️ Palpite em todos os jogos do grupo para simular "
                f"({info['palpitados']}/{info['total_jogos']})."
            )
            continue
        linhas = []
        for i, linha in enumerate(info["linhas"], start=1):
            marca = "✅" if i <= 2 else ("🟡" if i == 3 else "")
            nome_sel = selecoes[linha.selecao_id].nome_pt if linha.selecao_id in selecoes else "?"
            linhas.append(
                {
                    "#": i,
                    "Seleção": f"{marca} {nome_sel}".strip(),
                    "P": linha.pontos,
                    "J": linha.jogos,
                    "V": linha.vitorias,
                    "SG": linha.saldo,
                    "GP": linha.gols_pro,
                }
            )
        st.dataframe(pd.DataFrame(linhas), hide_index=True, use_container_width=True)

    st.caption("✅ classificados (1º e 2º) · 🟡 3º colocado (pode avançar como um dos 8 melhores)")


def render() -> None:
    usuario = sess.current_user()
    st.title("🌎 Minha Copa")
    aba_grupos, aba_mata = st.tabs(["🏆 Grupos", "🔥 Mata-mata"])
    with aba_grupos:
        _render_grupos(usuario.id)
    with aba_mata:
        st.info(
            "🔧 A simulação do mata-mata ficará disponível em breve: enquanto a fase de "
            "grupos não termina, mostrará uma prévia das 32avas conforme suas previsões; "
            "depois, a chave real com os times classificados."
        )
