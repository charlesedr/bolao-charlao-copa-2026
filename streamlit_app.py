import streamlit as st

from app.domain.enums import StatusUsuario
from app.ui import session as sess
from app.ui.views import admin, cadastro, login, palpites, pendente, ranking

st.set_page_config(page_title="Bolão Charlão Copa 2026", page_icon="🏆", layout="centered")

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
