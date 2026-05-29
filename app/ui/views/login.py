import streamlit as st
from sqlmodel import Session

from app.core.db import engine
from app.services import auth_service
from app.ui import session as sess


def render() -> None:
    st.title("🏆 Bolão Charlão Copa 2026")
    st.caption("Entre com seu apelido ou e-mail para palpitar.")

    with st.form("form_login"):
        login = st.text_input("Apelido ou e-mail")
        senha = st.text_input("Senha", type="password")
        enviar = st.form_submit_button("Entrar", use_container_width=True)

    if enviar:
        with Session(engine) as s:
            ok, msg, usuario = auth_service.autenticar(s, login=login, senha=senha)
        if not ok:
            st.error(msg)
        else:
            sess.login_session(usuario)
            st.rerun()

    st.divider()
    st.caption("Ainda não tem conta? Escolha **Cadastrar** no menu lateral.")
