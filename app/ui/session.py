"""Sessão do usuário: cookie persistente (JWT) + st.session_state.

A escrita do cookie (CookieController.set) funciona — o cookie aparece no
document.cookie do browser. O problema era a leitura: o controller fazia
cache do valor padrão ({}) no 1º run após F5. Chamamos `refresh()` a cada
run para re-invocar o componente; o auto-rerun do Streamlit traz o valor
real na sequência.
"""
import contextlib

import streamlit as st
from sqlmodel import Session
from streamlit_cookies_controller import CookieController

from app.core.db import engine
from app.core.security import criar_token, decodificar_token
from app.domain.models import Usuario
from app.repositories import user_repo

COOKIE = "bolao_token"
MAX_AGE = 7 * 24 * 3600  # 7 dias


def _ctrl() -> CookieController:
    if "_cookie_ctrl" not in st.session_state:
        st.session_state["_cookie_ctrl"] = CookieController()
    return st.session_state["_cookie_ctrl"]


def login_session(usuario: Usuario) -> None:
    st.session_state["user_id"] = usuario.id
    with contextlib.suppress(Exception):
        _ctrl().set(COOKIE, criar_token(usuario.id), max_age=MAX_AGE, same_site="lax")


def logout_session() -> None:
    st.session_state.pop("user_id", None)
    with contextlib.suppress(Exception):
        _ctrl().remove(COOKIE)


def cookies_detectados() -> list[str]:
    """Diagnóstico — nomes de cookies que o controller (com refresh) enxerga."""
    with contextlib.suppress(Exception):
        ctrl = _ctrl()
        ctrl.refresh()
        return sorted(ctrl.getAll().keys())
    return []


def current_user() -> Usuario | None:
    uid = st.session_state.get("user_id")
    if uid is None:
        with contextlib.suppress(Exception):
            ctrl = _ctrl()
            ctrl.refresh()  # força re-leitura do componente (evita cache do default)
            token = ctrl.get(COOKIE)
            if token:
                decoded = decodificar_token(token)
                if decoded:
                    uid = decoded
                    st.session_state["user_id"] = uid
    if uid is None:
        return None
    with Session(engine) as s:
        return user_repo.get_by_id(s, uid)
