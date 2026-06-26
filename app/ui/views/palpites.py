from datetime import date

import streamlit as st
from sqlalchemy import or_
from sqlmodel import Session, select

from app.core.db import engine
from app.core.timezone import format_brt, to_brt
from app.domain.enums import FasePartida, StatusPartida
from app.domain.models import Grupo, Partida
from app.repositories import bet_repo, match_repo
from app.services import bet_service, bracket_service
from app.ui import helpers
from app.ui import session as sess

GRUPOS = list("ABCDEFGHIJKL")
OPCOES_GRUPO = [*GRUPOS, "Mata-mata"]


def _carregar(data_filtro: date | None, grupos_sel: list[str]):
    with Session(engine) as s:
        inclui_mata = "Mata-mata" in grupos_sel
        if inclui_mata:
            bracket_service.resolver_32avos_parcial(s)

        selecoes = match_repo.mapa_selecoes(s)
        grupos = {g.id: g.nome for g in s.exec(select(Grupo)).all()}
        stmt = select(Partida).order_by(Partida.data_hora)
        if grupos_sel:
            letras = [g for g in grupos_sel if g != "Mata-mata"]
            conds = []
            if letras:
                gids = [gid for gid, nome in grupos.items() if nome in letras]
                conds.append(Partida.grupo_id.in_(gids))
            if "Mata-mata" in grupos_sel:
                conds.append(Partida.fase != FasePartida.GRUPOS)
            stmt = stmt.where(or_(*conds))
        partidas = list(s.exec(stmt).all())

    if data_filtro:
        partidas = [p for p in partidas if to_brt(p.data_hora).date() == data_filtro]
    if "Mata-mata" in grupos_sel:
        partidas = [
            p
            for p in partidas
            if p.fase == FasePartida.GRUPOS or (p.mandante_id and p.visitante_id)
        ]

    if not grupos_sel and not data_filtro:
        partidas = [
            p for p in partidas
            if p.mandante_id and p.status != StatusPartida.FINALIZADO
        ][:20]
    return selecoes, grupos, partidas


def _badge_palpite(palpite, is_mm: bool, selecoes) -> None:
    if palpite:
        extra = ""
        if is_mm and palpite.classificado_id in selecoes:
            extra = f" · classifica {selecoes[palpite.classificado_id].nome_pt}"
        st.markdown(
            "<div style='background:rgba(33,185,90,0.12); border:1px solid rgba(33,185,90,0.45); "
            "color:#21B95A; font-weight:600; padding:6px 10px; border-radius:8px; margin:4px 0 12px 0;'>"
            f"✅ Já palpitado: {palpite.gols_mandante} × {palpite.gols_visitante}{extra}"
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div style='background:rgba(242,180,65,0.10); border:1px solid rgba(242,180,65,0.45); "
            "color:#F2B441; font-weight:600; padding:6px 10px; border-radius:8px; margin:4px 0 12px 0;'>"
            "⚠️ Ainda sem palpite"
            "</div>",
            unsafe_allow_html=True,
        )


def _render_jogo_aberto(partida: Partida, selecoes, grupos, palpite) -> None:
    """Renderiza inputs de um jogo aberto (dentro de um form, sem submit)."""
    m = helpers.nome_time(selecoes, partida.mandante_id, partida.slot_mandante)
    v = helpers.nome_time(selecoes, partida.visitante_id, partida.slot_visitante)
    is_mm = partida.fase != FasePartida.GRUPOS

    with st.container(border=True):
        contexto = (
            f"Grupo {grupos[partida.grupo_id]}"
            if partida.grupo_id
            else helpers.FASE_LABEL.get(partida.fase, partida.fase)
        )
        st.caption(
            f"{contexto} · {format_brt(partida.data_hora)} BRT · {helpers.badge_status(partida)}"
        )
        _badge_palpite(palpite, is_mm, selecoes)

        st.markdown(f"**{m}**  ⚽  **{v}**")
        c1, c2 = st.columns(2)
        c1.number_input(
            m, min_value=0, max_value=30,
            value=palpite.gols_mandante if palpite else 0, key=f"gm_{partida.id}",
        )
        c2.number_input(
            v, min_value=0, max_value=30,
            value=palpite.gols_visitante if palpite else 0, key=f"gv_{partida.id}",
        )
        if is_mm:
            opcoes = [m, v]
            idx = 1 if (palpite and palpite.classificado_id == partida.visitante_id) else 0
            st.radio(
                "Empate nos 90 min: quem se classifica?",
                opcoes, index=idx, horizontal=True, key=f"cl_{partida.id}",
            )
        st.checkbox(
            "Marcar este jogo para salvar",
            value=bool(palpite),
            key=f"inc_{partida.id}",
            help="Marque para incluir no botão **Salvar palpites marcados**.",
        )


def _render_jogo_fechado(partida, selecoes, grupos, palpite, pont) -> None:
    m = helpers.nome_time(selecoes, partida.mandante_id, partida.slot_mandante)
    v = helpers.nome_time(selecoes, partida.visitante_id, partida.slot_visitante)
    is_mm = partida.fase != FasePartida.GRUPOS

    with st.container(border=True):
        contexto = (
            f"Grupo {grupos[partida.grupo_id]}"
            if partida.grupo_id
            else helpers.FASE_LABEL.get(partida.fase, partida.fase)
        )
        st.caption(
            f"{contexto} · {format_brt(partida.data_hora)} BRT · {helpers.badge_status(partida)}"
        )
        st.markdown(f"**{m}**  ⚽  **{v}**  🔒")
        if palpite:
            txt = f"Seu palpite: {palpite.gols_mandante} × {palpite.gols_visitante}"
            if is_mm and palpite.classificado_id in selecoes:
                txt += f" (classifica: {selecoes[palpite.classificado_id].nome_pt})"
            st.write(txt)
        else:
            st.write("_Você não palpitou neste jogo._")
        if partida.placar_mandante is not None:
            st.write(f"**Oficial: {partida.placar_mandante} × {partida.placar_visitante}**")
        if pont:
            st.success(f"Você fez **{pont.pontos_total}** ponto(s) neste jogo.")


def _salvar_marcados(abertos, usuario_id: int, selecoes) -> None:
    salvos = 0
    erros: list[str] = []
    with Session(engine) as s:
        for partida in abertos:
            if not st.session_state.get(f"inc_{partida.id}"):
                continue
            gm = int(st.session_state.get(f"gm_{partida.id}", 0))
            gv = int(st.session_state.get(f"gv_{partida.id}", 0))
            classificado_id = None
            is_mm = partida.fase != FasePartida.GRUPOS
            if is_mm and gm == gv:
                m_nome = helpers.nome_time(selecoes, partida.mandante_id, partida.slot_mandante)
                cl_choice = st.session_state.get(f"cl_{partida.id}")
                classificado_id = (
                    partida.mandante_id if cl_choice == m_nome else partida.visitante_id
                )
            ok, msg = bet_service.salvar_palpite(
                s, usuario_id=usuario_id, partida_id=partida.id,
                gols_mandante=gm, gols_visitante=gv, classificado_id=classificado_id,
            )
            if ok:
                salvos += 1
            else:
                erros.append(f"{partida.codigo}: {msg}")
    if salvos:
        st.toast(f"✅ {salvos} palpite(s) salvo(s)!", icon="✅")
    if erros:
        st.error("Alguns palpites **não** foram salvos:\n\n" + "\n".join(f"- {e}" for e in erros))


def render() -> None:
    usuario = sess.current_user()
    st.title("⚽ Palpites")

    c1, c2 = st.columns([1, 2])
    data_filtro = c1.date_input("Data (opcional)", value=None, format="DD/MM/YYYY")
    grupos_sel = c2.multiselect(
        "Grupos / fase (opcional, pode escolher mais de um)",
        options=OPCOES_GRUPO,
        default=[],
    )
    if not data_filtro and not grupos_sel:
        st.caption("Sem filtros: mostrando os **próximos 20 jogos** ainda não finalizados.")

    selecoes, grupos, partidas = _carregar(data_filtro, grupos_sel)
    if not partidas:
        if grupos_sel == ["Mata-mata"]:
            st.info("Nenhum confronto de mata-mata definido com os dois times ainda.")
            return
        st.info("Nenhum jogo para este filtro.")
        return

    with Session(engine) as s:
        palpites = {p.id: bet_repo.get(s, usuario.id, p.id) for p in partidas}
        pontuacoes = {p.id: bet_repo.pontuacao(s, usuario.id, p.id) for p in partidas}

    abertos = [p for p in partidas if bet_service.palpite_aberto(p)]
    fechados = [p for p in partidas if not bet_service.palpite_aberto(p)]

    if abertos:
        total_palpitados = sum(1 for p in abertos if palpites[p.id])
        st.markdown(
            f"📊 **{total_palpitados} de {len(abertos)}** jogos abertos já têm palpite. "
            "Edite os que quiser e clique em **Salvar palpites marcados** abaixo."
        )

        with st.form("bulk_palpites", clear_on_submit=False):
            salvar_topo = st.form_submit_button(
                "💾 Salvar palpites marcados", use_container_width=True
            )
            for partida in abertos:
                _render_jogo_aberto(partida, selecoes, grupos, palpites[partida.id])
            # Label diferente do botão de cima para evitar duplicidade de element key
            salvar_rodape = st.form_submit_button(
                "✅ Confirmar e salvar palpites marcados", use_container_width=True
            )

        if salvar_topo or salvar_rodape:
            _salvar_marcados(abertos, usuario.id, selecoes)
            st.rerun()

    if fechados:
        st.markdown("---")
        st.markdown("### 🔒 Jogos fechados / finalizados")
        for partida in fechados:
            _render_jogo_fechado(
                partida, selecoes, grupos, palpites[partida.id], pontuacoes[partida.id]
            )
