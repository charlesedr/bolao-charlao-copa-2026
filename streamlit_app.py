import os

import streamlit as st

st.set_page_config(page_title="Bolão Charlão Copa 2026", page_icon="🏆", layout="centered")

# Streamlit Community Cloud expõe segredos via st.secrets; replicamos para variáveis
# de ambiente para que o pydantic-settings (app.core.config) consiga lê-los.
try:
    for _chave, _valor in st.secrets.items():
        os.environ.setdefault(_chave, str(_valor))
except Exception:
    pass

from app.domain.enums import StatusUsuario  # noqa: E402
from app.ui import session as sess  # noqa: E402
from app.ui.views import (  # noqa: E402
    admin,
    aposta_final,
    cadastro,
    login,
    minha_copa,
    palpites,
    pendente,
    ranking,
)

usuario = sess.current_user()

if usuario is None:
    paginas = [
        st.Page(login.render, title="Entrar", icon="🔑", url_path="entrar", default=True),
        st.Page(cadastro.render, title="Cadastrar", icon="📝", url_path="cadastrar"),
    ]
elif usuario.status != StatusUsuario.APROVADO:
    paginas = [
        st.Page(pendente.render, title="Aguardando aprovação", icon="⏳",
                url_path="pendente", default=True)
    ]
else:
    paginas = [
        st.Page(palpites.render, title="Palpites", icon="⚽", url_path="palpites", default=True),
        st.Page(minha_copa.render, title="Minha Copa", icon="🌎", url_path="minha-copa"),
        st.Page(aposta_final.render, title="Aposta Final", icon="🏅", url_path="aposta-final"),
        st.Page(ranking.render, title="Ranking", icon="🏆", url_path="ranking"),
    ]
    if usuario.is_admin:
        paginas.append(st.Page(admin.render, title="Admin", icon="🛠️", url_path="admin"))

if usuario is not None:
    with st.sidebar:
        st.markdown(f"👤 **{usuario.apelido}**")
        if st.button("Sair", use_container_width=True):
            sess.logout_session()
            st.rerun()

st.navigation(paginas).run()
