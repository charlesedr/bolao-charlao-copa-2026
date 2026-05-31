import time

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
            # Pequeno respiro: deixa o componente de cookie flushar antes do rerun
            time.sleep(0.6)
            st.rerun()

    st.divider()
    st.caption("Ainda não tem conta? Escolha **Cadastrar** no menu lateral.")

    # Diagnóstico temporário: nomes de cookies visíveis pelo servidor
    detectados = sess.cookies_detectados()
    marca = "✅" if "bolao_token" in detectados else "❌"
    st.caption(f"🔧 diagnóstico — cookies vistos: {detectados or '(nenhum)'} · bolao_token: {marca}")
