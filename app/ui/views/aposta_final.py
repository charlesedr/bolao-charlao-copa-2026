import streamlit as st
from sqlmodel import Session

from app.core.db import engine
from app.repositories import match_repo
from app.services import aposta_service
from app.ui import session as sess


def render() -> None:
    usuario = sess.current_user()
    st.title("🏅 Aposta da Classificação Final")
    st.caption(
        "Aposte em campeão, vice, 3º e 4º lugar — 1 ponto por acerto (máx. 4). "
        "Trava 5 minutos antes do jogo de disputa do 3º lugar."
    )

    with Session(engine) as s:
        aberta = aposta_service.aposta_aberta(s)
        aposta = aposta_service.get_aposta(s, usuario.id)
        selecoes = sorted(match_repo.mapa_selecoes(s).values(), key=lambda x: x.nome_pt)

    nomes = [x.nome_pt for x in selecoes]
    ids = [x.id for x in selecoes]

    def _idx(sel_id: int | None) -> int:
        return ids.index(sel_id) if sel_id in ids else 0

    if not aberta:
        st.warning("⏰ As apostas estão encerradas.")

    with st.form("form_aposta"):
        c = st.selectbox("🥇 Campeão", nomes, index=_idx(aposta.campeao_id if aposta else None))
        v = st.selectbox("🥈 Vice-campeão", nomes, index=_idx(aposta.vice_id if aposta else None))
        t = st.selectbox("🥉 3º lugar", nomes, index=_idx(aposta.terceiro_id if aposta else None))
        q = st.selectbox("4️⃣ 4º lugar", nomes, index=_idx(aposta.quarto_id if aposta else None))
        salvar = st.form_submit_button(
            "Salvar aposta", use_container_width=True, disabled=not aberta
        )

    if salvar:
        with Session(engine) as s:
            ok, msg = aposta_service.salvar_aposta(
                s,
                usuario_id=usuario.id,
                campeao_id=ids[nomes.index(c)],
                vice_id=ids[nomes.index(v)],
                terceiro_id=ids[nomes.index(t)],
                quarto_id=ids[nomes.index(q)],
            )
        if ok:
            st.toast(msg, icon="✅")
            st.rerun()
        else:
            st.error(msg)

    if aposta and aposta.pontos_total:
        st.success(f"Sua aposta já pontuou: **{aposta.pontos_total}/4**")
