import streamlit as st
from sqlmodel import Session

from app.core.db import engine
from app.services import auth_service


def render() -> None:
    st.title("📝 Criar conta")
    st.caption("Após o cadastro, o administrador precisa aprovar você para liberar os palpites.")

    with st.form("form_cadastro"):
        nome = st.text_input("Nome")
        apelido = st.text_input("Apelido (usado no ranking e no login)")
        email = st.text_input("E-mail")
        telefone = st.text_input("Telefone/WhatsApp (com DDD)", placeholder="11 91234-5678")
        senha = st.text_input("Senha (mín. 6 caracteres)", type="password")
        senha2 = st.text_input("Confirme a senha", type="password")
        st.caption("📱 O telefone é usado para te adicionar ao grupo do WhatsApp do bolão.")
        enviar = st.form_submit_button("Cadastrar", use_container_width=True)

    if enviar:
        if senha != senha2:
            st.error("As senhas não conferem.")
            return
        with Session(engine) as s:
            ok, msg, _ = auth_service.cadastrar(
                s, nome=nome, apelido=apelido, email=email, telefone=telefone, senha=senha
            )
        if ok:
            st.success(msg)
            st.info("Volte ao menu **Entrar** após a aprovação.")
        else:
            st.error(msg)
