from datetime import date

import streamlit as st
from sqlalchemy import or_
from sqlmodel import Session, select

from app.core.db import engine
from app.core.timezone import format_brt, to_brt
from app.domain.enums import FasePartida, StatusPartida
from app.domain.models import Grupo, Partida
from app.repositories import bet_repo, match_repo
from app.services import bet_service
from app.ui import helpers
from app.ui import session as sess

GRUPOS = list("ABCDEFGHIJKL")
OPCOES_GRUPO = [*GRUPOS, "Mata-mata"]


def _carregar(data_filtro: date | None, grupos_sel: list[str]):
    with Session(engine) as s:
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

    # Sem nenhum filtro -> próximos 20 não-finalizados com times definidos
    if not grupos_sel and not data_filtro:
        partidas = [
            p for p in partidas
            if p.mandante_id and p.status != StatusPartida.FINALIZADO
        ][:20]

    return selecoes, grupos, partidas


def _render_jogo(partida: Partida, selecoes, grupos, usuario_id: int) -> None:
    m = helpers.nome_time(selecoes, partida.mandante_id, partida.slot_mandante)
    v = helpers.nome_time(selecoes, partida.visitante_id, partida.slot_visitante)
    is_mm = partida.fase != FasePartida.GRUPOS
    aberto = bet_service.palpite_aberto(partida)

    with Session(engine) as s:
        palpite = bet_repo.get(s, usuario_id, partida.id)
        pont = bet_repo.pontuacao(s, usuario_id, partida.id)

    with st.container(border=True):
        contexto = (
            f"Grupo {grupos[partida.grupo_id]}"
            if partida.grupo_id
            else helpers.FASE_LABEL.get(partida.fase, partida.fase)
        )
        st.caption(
            f"{contexto} · {format_brt(partida.data_hora)} BRT · {helpers.badge_status(partida)}"
        )

        if aberto:
            with st.form(f"jogo_{partida.id}"):
                st.markdown(f"**{m}**  ⚽  **{v}**")
                c1, c2 = st.columns(2)
                gm = c1.number_input(
                    m, min_value=0, max_value=30,
                    value=palpite.gols_mandante if palpite else 0, key=f"gm_{partida.id}",
                )
                gv = c2.number_input(
                    v, min_value=0, max_value=30,
                    value=palpite.gols_visitante if palpite else 0, key=f"gv_{partida.id}",
                )
                classificado_id = None
                if is_mm:
                    opcoes = {m: partida.mandante_id, v: partida.visitante_id}
                    idx = 1 if (palpite and palpite.classificado_id == partida.visitante_id) else 0
                    escolha = st.radio(
                        "Empate nos 90 min: quem se classifica?",
                        list(opcoes.keys()), index=idx, horizontal=True, key=f"cl_{partida.id}",
                    )
                    classificado_id = opcoes[escolha]
                salvar = st.form_submit_button("Salvar palpite", use_container_width=True)

            if salvar:
                with Session(engine) as s:
                    ok, msg = bet_service.salvar_palpite(
                        s, usuario_id=usuario_id, partida_id=partida.id,
                        gols_mandante=int(gm), gols_visitante=int(gv),
                        classificado_id=classificado_id,
                    )
                if ok:
                    st.toast(msg, icon="✅")
                    st.rerun()
                else:
                    st.error(msg)
        else:
            st.markdown(f"**{m}**  ⚽  **{v}**  🔒")
            if palpite:
                txt = f"Seu palpite: {palpite.gols_mandante} x {palpite.gols_visitante}"
                if is_mm and palpite.classificado_id in selecoes:
                    txt += f" (classifica: {selecoes[palpite.classificado_id].nome_pt})"
                st.write(txt)
            else:
                st.write("_Você não palpitou neste jogo._")
            if partida.placar_mandante is not None:
                st.write(f"**Oficial: {partida.placar_mandante} x {partida.placar_visitante}**")
            if pont:
                st.success(f"Você fez **{pont.pontos_total}** ponto(s) neste jogo.")


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
        st.info("Nenhum jogo para este filtro.")
        return
    for partida in partidas:
        _render_jogo(partida, selecoes, grupos, usuario.id)
