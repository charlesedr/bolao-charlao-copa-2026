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
    # Marca um flag "acabei de sair" para o próximo run pular a auto-restauração via cookie
    st.session_state["_just_logged_out"] = True
    st.session_state.pop("user_id", None)
    with contextlib.suppress(Exception):
        _ctrl().remove(COOKIE)
    # Limpa o cookie do cache interno do controller para evitar reler valor stale
    with contextlib.suppress(Exception):
        cache = st.session_state.get("cookies")
        if isinstance(cache, dict) and COOKIE in cache:
            del cache[COOKIE]


def cookies_detectados() -> list[str]:
    """Diagnóstico — nomes de cookies que o controller (com refresh) enxerga."""
    with contextlib.suppress(Exception):
        ctrl = _ctrl()
        ctrl.refresh()
        return sorted(ctrl.getAll().keys())
    return []


def current_user() -> Usuario | None:
    # Se acabamos de sair, ignora o cookie neste run (evita auto-restauração indesejada)
    if st.session_state.pop("_just_logged_out", False):
        return None

    uid = st.session_state.get("user_id")
    if uid is None:
        with contextlib.suppress(Exception):
            ctrl = _ctrl()
            ctrl.refresh()
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
