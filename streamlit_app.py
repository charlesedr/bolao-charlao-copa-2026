import contextlib
import os

import streamlit as st
import streamlit.components.v1 as components

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
from app.ui.theme import aplicar_tema  # noqa: E402
from app.ui.views import (  # noqa: E402
    admin,
    ajuda,
    aposta_final,
    cadastro,
    comparar,
    guia,
    login,
    minha_copa,
    palpites,
    pendente,
    perfil,
    ranking,
    tela_partida,
)

aplicar_tema()

# Estado de carregamento: no 1º run de uma sessão (após F5 ou primeira visita),
# espera o componente de cookie sincronizar antes de montar a navegação.
# Isso evita o popup "Page not found" quando a URL é de uma página protegida
# e o cookie ainda não foi lido.
_em_loading = (
    "user_id" not in st.session_state
    and not st.session_state.get("_session_attempted")
    and "noload" not in st.query_params
)
if _em_loading:
    st.session_state["_session_attempted"] = True
    # Dispara o componente para sincronizar com o browser
    with contextlib.suppress(Exception):
        sess._ctrl().refresh()
    st.markdown(
        "<div style='text-align:center; padding:4rem; color:#E8B53D;'>"
        "<h2 style='font-family:Anton,sans-serif; letter-spacing:1px;'>🏆 Carregando…</h2>"
        "</div>",
        unsafe_allow_html=True,
    )
    # Fallback: se o browser não tiver o cookie, recarrega com flag p/ pular o loading
    components.html(
        """
        <script>
        setTimeout(() => {
            try {
                const has = document.cookie.split(';').some(
                    c => c.trim().startsWith('bolao_token=')
                );
                if (!has) {
                    const u = new URL(window.parent.location.href);
                    if (!u.searchParams.has('noload')) {
                        u.searchParams.set('noload', '1');
                        window.parent.location.replace(u.toString());
                    }
                }
            } catch(e) {}
        }, 1200);
        </script>
        """,
        height=0,
    )
    st.stop()

# Garante que o flag de "session_attempted" fica setado mesmo no bypass via ?noload
st.session_state.setdefault("_session_attempted", True)

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
        st.Page(tela_partida.render, title="Tela da Partida", icon="📋", url_path="partida"),
        st.Page(comparar.render, title="Comparar", icon="⚔️", url_path="comparar"),
        st.Page(perfil.render, title="Perfil", icon="👤", url_path="perfil"),
        st.Page(guia.render, title="Guia rápido", icon="📚", url_path="guia"),
        st.Page(ajuda.render, title="Como Funciona", icon="❓", url_path="ajuda"),
    ]
    if usuario.is_admin:
        paginas.append(st.Page(admin.render, title="Admin", icon="🛠️", url_path="admin"))

if usuario is not None:
    with st.sidebar:
        st.markdown("### 🏆 Bolão Charlão")
        st.caption("Copa do Mundo FIFA 2026")
        st.markdown(f"👤 **{usuario.apelido}**")
        if st.button("Sair", use_container_width=True):
            sess.logout_session()
            st.rerun()

st.navigation(paginas).run()
