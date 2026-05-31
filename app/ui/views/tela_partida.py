from datetime import date

import pandas as pd
import streamlit as st
from sqlalchemy import or_
from sqlmodel import Session, select

from app.core.db import engine
from app.core.timezone import format_brt, now_utc, to_brt
from app.domain.enums import FasePartida, StatusUsuario
from app.domain.models import Grupo, Partida
from app.repositories import bet_repo, match_repo, user_repo
from app.ui import helpers
from app.ui import session as sess

GRUPOS = list("ABCDEFGHIJKL")
OPCOES_GRUPO = [*GRUPOS, "Mata-mata"]


def _filtrar_partidas(data_filtro: date | None, grupos_sel: list[str]):
    with Session(engine) as s:
        grupos = {g.id: g.nome for g in s.exec(select(Grupo)).all()}
        stmt = select(Partida).where(Partida.mandante_id.is_not(None)).order_by(Partida.data_hora)
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
    return partidas


def render() -> None:
    sess.current_user()
    st.title("📋 Tela da Partida")

    c1, c2 = st.columns([1, 2])
    data_filtro = c1.date_input("Data (opcional)", value=None, format="DD/MM/YYYY")
    grupos_sel = c2.multiselect(
        "Grupos / fase (opcional, pode escolher mais de um)",
        options=OPCOES_GRUPO,
        default=[],
    )

    with Session(engine) as s:
        selecoes = match_repo.mapa_selecoes(s)

    partidas = _filtrar_partidas(data_filtro, grupos_sel)
    if not partidas:
        st.info("Nenhum jogo encontrado com esse filtro.")
        return

    rotulos = {
        f"{p.codigo} · {helpers.label_partida(p, selecoes)}": p.id for p in partidas
    }
    escolha = st.selectbox("Escolha o jogo", list(rotulos.keys()))
    pid = rotulos[escolha]

    with Session(engine) as s:
        p = match_repo.get(s, pid)
        m = helpers.nome_time(selecoes, p.mandante_id, p.slot_mandante)
        v = helpers.nome_time(selecoes, p.visitante_id, p.slot_visitante)
        st.subheader(f"{m} x {v}")
        st.caption(f"{format_brt(p.data_hora)} BRT · {helpers.badge_status(p)}")
        if p.placar_mandante is not None:
            st.markdown(f"### Resultado oficial: {p.placar_mandante} × {p.placar_visitante}")

        palpites = bet_repo.listar_por_partida(s, pid)
        iniciado = now_utc() >= p.data_hora

        if not iniciado:
            st.info(
                f"🔒 {len(palpites)} palpite(s) registrados. "
                "Os palpites de todos ficam visíveis após o início do jogo."
            )
            return

        usuarios = {u.id: u for u in user_repo.listar(s)}
        linhas = []
        for pal in palpites:
            u = usuarios.get(pal.usuario_id)
            if not u or u.status != StatusUsuario.APROVADO:
                continue
            pont = bet_repo.pontuacao(s, pal.usuario_id, pid)
            extra = ""
            if pal.classificado_id in selecoes and p.fase != FasePartida.GRUPOS:
                extra = f" (→ {selecoes[pal.classificado_id].nome_pt})"
            linhas.append(
                {
                    "Apelido": u.apelido,
                    "Palpite": f"{pal.gols_mandante}×{pal.gols_visitante}{extra}",
                    "Pontos": pont.pontos_total if pont else 0,
                }
            )

    if linhas:
        df = pd.DataFrame(sorted(linhas, key=lambda x: -x["Pontos"]))
        st.dataframe(df, hide_index=True, use_container_width=True)
    else:
        st.info("Ninguém palpitou neste jogo.")
