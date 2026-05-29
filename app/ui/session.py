"""Sessão do usuário: cookie persistente (JWT) + st.session_state."""
import contextlib

import streamlit as st
from sqlmodel import Session
from streamlit_cookies_controller import CookieController

from app.core.db import engine
from app.core.security import criar_token, decodificar_token
from app.domain.models import Usuario
from app.repositories import user_repo

COOKIE = "bolao_token"


def _ctrl() -> CookieController:
    if "_cookie_ctrl" not in st.session_state:
        st.session_state["_cookie_ctrl"] = CookieController()
    return st.session_state["_cookie_ctrl"]


def login_session(usuario: Usuario) -> None:
    st.session_state["user_id"] = usuario.id
    with contextlib.suppress(Exception):
        _ctrl().set(COOKIE, criar_token(usuario.id))


def logout_session() -> None:
    st.session_state.pop("user_id", None)
    with contextlib.suppress(Exception):
        _ctrl().remove(COOKIE)


def current_user() -> Usuario | None:
    uid = st.session_state.get("user_id")
    if uid is None:
        token = None
        with contextlib.suppress(Exception):
            token = _ctrl().get(COOKIE)
        if token:
            decoded = decodificar_token(token)
            if decoded:
                uid = decoded
                st.session_state["user_id"] = uid
    if uid is None:
        return None
    with Session(engine) as s:
        return user_repo.get_by_id(s, uid)
