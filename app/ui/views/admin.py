import streamlit as st
from sqlmodel import Session, select

from app.core.db import engine
from app.core.timezone import format_brt
from app.domain.enums import FasePartida, StatusPartida, StatusUsuario
from app.domain.models import Partida
from app.repositories import match_repo, user_repo
from app.services import admin_service, match_service
from app.ui import helpers
from app.ui import session as sess

STATUS_LABEL = {
    StatusPartida.NAO_INICIADO: "Não iniciado",
    StatusPartida.EM_ANDAMENTO: "Em andamento",
    StatusPartida.FINALIZADO: "Finalizado",
}


def _aba_usuarios(admin_id: int) -> None:
    filtro = st.selectbox(
        "Filtrar por status",
        ["pendente", "aprovado", "bloqueado", "reprovado", "(todos)"],
    )
    with Session(engine) as s:
        usuarios = user_repo.listar(s, None if filtro == "(todos)" else filtro)

    if not usuarios:
        st.info("Nenhum usuário neste filtro.")
        return

    for u in usuarios:
        with st.container(border=True):
            st.markdown(f"**{u.apelido}** · {u.nome} · {u.email}")
            st.caption(f"Status: {u.status}{' · ADMIN' if u.is_admin else ''}")
            cols = st.columns(4)
            acao = None
            if u.status == StatusUsuario.PENDENTE:
                if cols[0].button("Aprovar", key=f"ap_{u.id}"):
                    acao = ("aprovar", u.id)
                if cols[1].button("Reprovar", key=f"rp_{u.id}"):
                    acao = ("reprovar", u.id)
            elif u.status == StatusUsuario.APROVADO and not u.is_admin:
                if cols[0].button("Bloquear", key=f"bl_{u.id}"):
                    acao = ("bloquear", u.id)
            elif u.status == StatusUsuario.BLOQUEADO:
                if cols[0].button("Desbloquear", key=f"db_{u.id}"):
                    acao = ("desbloquear", u.id)
            if cols[3].button("Resetar senha", key=f"rs_{u.id}"):
                acao = ("reset", u.id)

            if acao:
                nome_acao, uid = acao
                with Session(engine) as s:
                    fn = {
                        "aprovar": admin_service.aprovar,
                        "reprovar": admin_service.reprovar,
                        "bloquear": admin_service.bloquear,
                        "desbloquear": admin_service.desbloquear,
                        "reset": admin_service.resetar_senha,
                    }[nome_acao]
                    ok, msg = fn(s, admin_id=admin_id, usuario_id=uid)
                if ok:
                    st.toast(msg, icon="✅")
                    if nome_acao == "reset":
                        st.warning(msg)
                    else:
                        st.rerun()
                else:
                    st.error(msg)


def _aba_resultados(admin_id: int) -> None:
    with Session(engine) as s:
        selecoes = match_repo.mapa_selecoes(s)
        partidas = list(
            s.exec(
                select(Partida)
                .where(Partida.mandante_id.is_not(None))
                .order_by(Partida.data_hora)
            ).all()
        )

    if not partidas:
        st.info("Nenhuma partida com times definidos ainda.")
        return

    rotulos = {
        f"{p.codigo} · {helpers.nome_time(selecoes, p.mandante_id, p.slot_mandante)} x "
        f"{helpers.nome_time(selecoes, p.visitante_id, p.slot_visitante)} · "
        f"{format_brt(p.data_hora)}": p
        for p in partidas
    }
    escolha = st.selectbox("Partida", list(rotulos.keys()))
    p = rotulos[escolha]
    is_mm = p.fase != FasePartida.GRUPOS
    m = helpers.nome_time(selecoes, p.mandante_id, p.slot_mandante)
    v = helpers.nome_time(selecoes, p.visitante_id, p.slot_visitante)

    st.caption("Lance o placar dos **90 minutos** (prorrogação/pênaltis só definem o classificado).")
    with st.form("form_resultado"):
        c1, c2 = st.columns(2)
        pm = c1.number_input(m, min_value=0, max_value=30, value=p.placar_mandante or 0)
        pv = c2.number_input(v, min_value=0, max_value=30, value=p.placar_visitante or 0)
        status = st.selectbox(
            "Status", list(STATUS_LABEL.keys()),
            format_func=lambda x: STATUS_LABEL[x],
            index=list(STATUS_LABEL.keys()).index(p.status),
        )
        classificado_id = None
        if is_mm:
            opcoes = {m: p.mandante_id, v: p.visitante_id}
            idx = 1 if p.classificado_id == p.visitante_id else 0
            escolha_cl = st.radio(
                "Quem se classificou? (use em caso de empate nos 90 min)",
                list(opcoes.keys()), index=idx, horizontal=True,
            )
            classificado_id = opcoes[escolha_cl]
        salvar = st.form_submit_button("Salvar e recalcular", use_container_width=True)

    if salvar:
        with Session(engine) as s:
            ok, msg = match_service.lancar_placar(
                s, admin_id=admin_id, partida_id=p.id,
                placar_mandante=int(pm), placar_visitante=int(pv),
                classificado_id=classificado_id, status=status,
            )
        (st.success if ok else st.error)(msg)


def _aba_saude(admin_id: int) -> None:
    with Session(engine) as s:
        partidas = match_repo.listar(s)
        sem_resultado = sum(1 for p in partidas if p.placar_mandante is None)
        pendentes = len(user_repo.listar(s, StatusUsuario.PENDENTE))
    c1, c2 = st.columns(2)
    c1.metric("Jogos sem resultado", sem_resultado)
    c2.metric("Usuários pendentes", pendentes)
    if st.button("Recalcular pontuação geral"):
        with Session(engine) as s:
            n = match_service.recalcular_tudo(s)
        st.success(f"Recalculados {n} jogos.")


def render() -> None:
    usuario = sess.current_user()
    st.title("🛠️ Administração")
    aba1, aba2, aba3 = st.tabs(["Usuários", "Resultados", "Saúde"])
    with aba1:
        _aba_usuarios(usuario.id)
    with aba2:
        _aba_resultados(usuario.id)
    with aba3:
        _aba_saude(usuario.id)
