import re

import streamlit as st
from sqlmodel import Session, select

from app.core.db import engine
from app.core.timezone import format_brt
from app.domain.enums import FasePartida, StatusPartida, StatusUsuario
from app.domain.models import Partida
from app.repositories import match_repo, user_repo
from app.services import admin_service, bracket_service, match_service
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
            st.markdown(f"**{u.apelido}** · {u.nome}")
            st.caption(f"{u.email} · Status: {u.status}{' · ADMIN' if u.is_admin else ''}")
            if u.telefone:
                digitos = re.sub(r"\D", "", u.telefone)
                if len(digitos) in (10, 11):
                    digitos = "55" + digitos
                st.markdown(f"📱 {u.telefone} — [abrir no WhatsApp](https://wa.me/{digitos})")
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

            # Excluir (apenas reprovado/bloqueado, com confirmação dupla)
            if not u.is_admin and u.status in (
                StatusUsuario.REPROVADO, StatusUsuario.BLOQUEADO,
            ):
                conf_key = f"conf_del_{u.id}"
                rotulo = "Confirmar exclusão?" if st.session_state.get(conf_key) else "🗑️ Excluir"
                if cols[2].button(rotulo, key=f"del_{u.id}"):
                    if st.session_state.pop(conf_key, False):
                        acao = ("excluir", u.id)
                    else:
                        st.session_state[conf_key] = True
                        st.rerun()

            if acao:
                nome_acao, uid = acao
                with Session(engine) as s:
                    fn = {
                        "aprovar": admin_service.aprovar,
                        "reprovar": admin_service.reprovar,
                        "bloquear": admin_service.bloquear,
                        "desbloquear": admin_service.desbloquear,
                        "reset": admin_service.resetar_senha,
                        "excluir": admin_service.excluir_usuario,
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

    rotulos = [
        (
            f"{p.codigo} · {helpers.nome_time(selecoes, p.mandante_id, p.slot_mandante)} x "
            f"{helpers.nome_time(selecoes, p.visitante_id, p.slot_visitante)} · "
            f"{format_brt(p.data_hora)}",
            p,
        )
        for p in partidas
    ]
    # Em andamento primeiro, senão a próxima a começar.
    indice_default = helpers.indice_partida_default(partidas, prefer_em_andamento=True)
    escolha = st.selectbox(
        "Partida",
        options=[r[0] for r in rotulos],
        index=indice_default,
    )
    p = next(p for label, p in rotulos if label == escolha)
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

        # Cartões (fair play) — opcional; usado no desempate dos 3º colocados
        with st.expander("🟨 Cartões (Fair Play) — opcional, usado em desempate dos 3º"):
            st.caption(
                "Preencha apenas se forem necessários para desempate. "
                "Cada amarelo = −1, vermelho indireto (2º amarelo) = −3, "
                "vermelho direto = −4, amarelo + vermelho direto (mesmo jogador) = −5."
            )
            fc1, fc2 = st.columns(2)
            fc1.markdown(f"**{m}**")
            fp_am_m = fc1.number_input(
                "Cartões amarelos", min_value=0, max_value=22,
                value=p.fp_amarelos_mandante, key=f"fp_am_m_{p.id}",
            )
            fp_2a_m = fc1.number_input(
                "Vermelho por 2º amarelo (indireto)", min_value=0, max_value=11,
                value=p.fp_verm_2amarelo_mandante, key=f"fp_2a_m_{p.id}",
            )
            fp_vd_m = fc1.number_input(
                "Vermelho direto", min_value=0, max_value=11,
                value=p.fp_verm_direto_mandante, key=f"fp_vd_m_{p.id}",
            )
            fp_av_m = fc1.number_input(
                "Amarelo + Vermelho direto (mesmo jogador)", min_value=0, max_value=11,
                value=p.fp_amarelo_verm_mandante, key=f"fp_av_m_{p.id}",
            )
            fc2.markdown(f"**{v}**")
            fp_am_v = fc2.number_input(
                "Cartões amarelos", min_value=0, max_value=22,
                value=p.fp_amarelos_visitante, key=f"fp_am_v_{p.id}",
            )
            fp_2a_v = fc2.number_input(
                "Vermelho por 2º amarelo (indireto)", min_value=0, max_value=11,
                value=p.fp_verm_2amarelo_visitante, key=f"fp_2a_v_{p.id}",
            )
            fp_vd_v = fc2.number_input(
                "Vermelho direto", min_value=0, max_value=11,
                value=p.fp_verm_direto_visitante, key=f"fp_vd_v_{p.id}",
            )
            fp_av_v = fc2.number_input(
                "Amarelo + Vermelho direto (mesmo jogador)", min_value=0, max_value=11,
                value=p.fp_amarelo_verm_visitante, key=f"fp_av_v_{p.id}",
            )

        salvar = st.form_submit_button("Salvar e recalcular", use_container_width=True)

    if salvar:
        with Session(engine) as s:
            ok, msg = match_service.lancar_placar(
                s, admin_id=admin_id, partida_id=p.id,
                placar_mandante=int(pm), placar_visitante=int(pv),
                classificado_id=classificado_id, status=status,
                fp_amarelos_mandante=int(fp_am_m),
                fp_verm_2amarelo_mandante=int(fp_2a_m),
                fp_verm_direto_mandante=int(fp_vd_m),
                fp_amarelo_verm_mandante=int(fp_av_m),
                fp_amarelos_visitante=int(fp_am_v),
                fp_verm_2amarelo_visitante=int(fp_2a_v),
                fp_verm_direto_visitante=int(fp_vd_v),
                fp_amarelo_verm_visitante=int(fp_av_v),
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

    if st.button("Preencher 32avos (a partir dos grupos)"):
        with Session(engine) as s:
            ok, msg = bracket_service.resolver_32avos(s)
        (st.success if ok else st.warning)(msg)


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
