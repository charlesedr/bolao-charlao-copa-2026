"""Sessão do usuário: cookie persistente (JWT) + st.session_state.

Usa `streamlit-cookies-manager` (componente síncrono com `ready()`),
que lida corretamente com o sync do componente após F5/refresh.
"""
import contextlib

import streamlit as st
from sqlmodel import Session
from streamlit_cookies_manager import CookieManager

from app.core.db import engine
from app.core.security import criar_token, decodificar_token
from app.domain.models import Usuario
from app.repositories import user_repo

COOKIE = "bolao_token"


def _cookies() -> CookieManager:
    if "_ckmgr" not in st.session_state:
        st.session_state["_ckmgr"] = CookieManager(prefix="")
    return st.session_state["_ckmgr"]


def _aguardar_ready() -> CookieManager:
    """Garante que o componente sincronizou os cookies do browser.

    No 1º run após F5 retorna ready=False e chama st.stop(); o componente
    sincroniza no frontend e dispara um auto-rerun, no qual ready=True.
    """
    cookies = _cookies()
    if not cookies.ready():
        st.stop()
    return cookies


def login_session(usuario: Usuario) -> None:
    st.session_state["user_id"] = usuario.id
    with contextlib.suppress(Exception):
        cookies = _cookies()
        if cookies.ready():
            cookies[COOKIE] = criar_token(usuario.id)
            cookies.save()


def logout_session() -> None:
    st.session_state.pop("user_id", None)
    with contextlib.suppress(Exception):
        cookies = _cookies()
        if cookies.ready() and COOKIE in cookies:
            del cookies[COOKIE]
            cookies.save()


def cookies_detectados() -> list[str]:
    """Diagnóstico — nomes de cookies vistos pelo cookie manager."""
    with contextlib.suppress(Exception):
        cookies = _cookies()
        if cookies.ready():
            return sorted(cookies.keys())
    return []


def current_user() -> Usuario | None:
    uid = st.session_state.get("user_id")
    if uid is None:
        cookies = _aguardar_ready()  # interrompe o 1º run; volta no auto-rerun
        token = cookies.get(COOKIE)
        if token:
            decoded = decodificar_token(token)
            if decoded:
                uid = decoded
                st.session_state["user_id"] = uid
    if uid is None:
        return None
    with Session(engine) as s:
        return user_repo.get_by_id(s, uid)
