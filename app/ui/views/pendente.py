import streamlit as st

from app.services import auth_service
from app.ui import session as sess


def render() -> None:
    usuario = sess.current_user()
    st.title("⏳ Aguardando aprovação")
    if usuario:
        msg = auth_service.mensagem_por_status(usuario)
        st.info(msg or "Acesso não autorizado.")
    st.caption("Assim que o administrador aprovar, seus palpites serão liberados.")
    if st.button("Sair"):
        sess.logout_session()
        st.rerun()
