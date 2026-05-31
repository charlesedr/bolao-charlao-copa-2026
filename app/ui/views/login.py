import time

import streamlit as st
import streamlit.components.v1 as components
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

    # Diagnóstico temporário: o que SERVIDOR vê (via cabeçalho da requisição)
    detectados = sess.cookies_detectados()
    marca = "✅" if "bolao_token" in detectados else "❌"
    st.caption(
        f"🔧 server (st.context.cookies): {detectados or '(nenhum)'} · bolao_token: {marca}"
    )

    # Diagnóstico temporário: o que o BROWSER tem (document.cookie via JS)
    components.html(
        """
        <div style="color:#e8b53d; font:12px monospace; padding:4px 8px;">
          🍪 browser (document.cookie):
          <span id="ckdiag" style="color:#fff;">(carregando…)</span>
        </div>
        <script>
          const el = document.getElementById('ckdiag');
          try {
            const c = document.cookie;
            const tem = c.includes('bolao_token');
            el.innerText = (c || '(vazio)') + '  ·  bolao_token: ' + (tem ? '✅' : '❌');
          } catch(e) { el.innerText = 'erro: ' + e; }
        </script>
        """,
        height=46,
    )
