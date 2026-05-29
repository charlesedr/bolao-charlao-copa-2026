import pandas as pd
import streamlit as st
from sqlmodel import Session

from app.core.db import engine
from app.domain.enums import FasePartida
from app.repositories import bet_repo, match_repo
from app.services import simulation_service
from app.ui import helpers
from app.ui import session as sess

FASES_MATA = [
    FasePartida.R32,
    FasePartida.OITAVAS,
    FasePartida.QUARTAS,
    FasePartida.SEMIFINAL,
    FasePartida.DISPUTA_3O,
    FasePartida.FINAL,
]


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


def _render_bracket_real(s: Session, usuario_id: int) -> None:
    st.caption("Chave **real** com os times classificados + os seus palpites.")
    selecoes = match_repo.mapa_selecoes(s)
    for fase in FASES_MATA:
        jogos = match_repo.listar(s, fase)
        if not jogos:
            continue
        st.subheader(helpers.FASE_LABEL.get(fase, fase))
        for p in jogos:
            m = helpers.nome_time(selecoes, p.mandante_id, p.slot_mandante)
            v = helpers.nome_time(selecoes, p.visitante_id, p.slot_visitante)
            texto = f"**{m}** x **{v}**"
            if p.placar_mandante is not None:
                texto += f" — oficial {p.placar_mandante}×{p.placar_visitante}"
            palpite = bet_repo.get(s, usuario_id, p.id)
            if palpite:
                texto += f" · seu palpite {palpite.gols_mandante}×{palpite.gols_visitante}"
            st.write(texto)


def _render_mata(usuario_id: int) -> None:
    with Session(engine) as s:
        grupos_real = match_repo.listar(s, FasePartida.GRUPOS)
        real_finalizado = bool(grupos_real) and all(
            p.placar_mandante is not None for p in grupos_real
        )
        if real_finalizado:
            _render_bracket_real(s, usuario_id)
            return
        pares, msg = simulation_service.simular_mata_mata(s, usuario_id)

    if pares is None:
        st.info(msg)
        return
    st.caption(f"🔮 {msg}")
    st.markdown("**Suas 32avas de final:**")
    for par in pares:
        st.write(f"{par['mandante']}  x  {par['visitante']}")


def render() -> None:
    usuario = sess.current_user()
    st.title("🌎 Minha Copa")
    aba_grupos, aba_mata = st.tabs(["🏆 Grupos", "🔥 Mata-mata"])
    with aba_grupos:
        _render_grupos(usuario.id)
    with aba_mata:
        _render_mata(usuario.id)
