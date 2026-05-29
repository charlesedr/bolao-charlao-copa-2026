import pandas as pd
import streamlit as st
from sqlmodel import Session

from app.core.db import engine
from app.core.timezone import format_brt, now_utc
from app.domain.enums import StatusUsuario
from app.repositories import bet_repo, match_repo, user_repo
from app.ui import helpers
from app.ui import session as sess


def render() -> None:
    sess.current_user()
    st.title("📋 Tela da Partida")

    with Session(engine) as s:
        selecoes = match_repo.mapa_selecoes(s)
        partidas = sorted(match_repo.listar(s), key=lambda p: p.data_hora)
        rotulos = {
            f"{p.codigo} · {helpers.label_partida(p, selecoes)}": p.id
            for p in partidas
            if p.mandante_id
        }

    if not rotulos:
        st.info("Nenhum jogo com times definidos ainda.")
        return

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
            if pal.classificado_id in selecoes and p.fase != "grupos":
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
