"""Sessão do usuário: cookie persistente (JWT) + st.session_state.

Leitura do cookie via st.context.cookies (cabeçalho da requisição — confiável após F5);
gravação/remoção via componente CookieController.
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
MAX_AGE = 7 * 24 * 3600  # 7 dias em segundos


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


def _ler_cookie() -> str | None:
    # 1) Leitura via cabeçalho da requisição — disponível já no 1º run após F5
    with contextlib.suppress(Exception):
        token = st.context.cookies.get(COOKIE)
        if token:
            return token
    # 2) Fallback pelo componente
    with contextlib.suppress(Exception):
        return _ctrl().get(COOKIE)
    return None


def cookies_detectados() -> list[str]:
    """Lista nomes de cookies que o servidor enxerga (diagnóstico)."""
    with contextlib.suppress(Exception):
        return sorted(st.context.cookies.keys())
    return []


def current_user() -> Usuario | None:
    uid = st.session_state.get("user_id")
    if uid is None:
        token = _ler_cookie()
        if token:
            decoded = decodificar_token(token)
            if decoded:
                uid = decoded
                st.session_state["user_id"] = uid
    if uid is None:
        return None
    with Session(engine) as s:
        return user_repo.get_by_id(s, uid)
