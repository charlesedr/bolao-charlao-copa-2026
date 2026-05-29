import streamlit as st
from sqlmodel import Session

from app.core.db import engine
from app.core.timezone import now_utc
from app.domain.enums import StatusUsuario
from app.repositories import bet_repo, match_repo, user_repo
from app.services import ranking_service
from app.ui import helpers
from app.ui import session as sess


def render() -> None:
    sess.current_user()
    st.title("👤 Perfil do participante")

    with Session(engine) as s:
        aprovados = user_repo.listar(s, StatusUsuario.APROVADO)

    if not aprovados:
        st.info("Nenhum participante aprovado ainda.")
        return

    nomes = {u.apelido: u.id for u in aprovados}
    escolha = st.selectbox("Participante", list(nomes.keys()))
    uid = nomes[escolha]

    with Session(engine) as s:
        u = user_repo.get_by_id(s, uid)
        ranking = ranking_service.ranking(s)
        info = next((r for r in ranking if r["usuario_id"] == uid), None)
        selecoes = match_repo.mapa_selecoes(s)
        partidas = {p.id: p for p in match_repo.listar(s)}
        palpites = bet_repo.listar_por_usuario(s, uid)

        st.subheader(u.apelido)
        st.caption(u.nome)
        if info:
            st.metric("Pontos", info["pontos"], f"{info['posicao']}º lugar")

        st.markdown("**Palpites (jogos já iniciados):**")
        agora = now_utc()
        linhas = []
        for pal in palpites:
            p = partidas.get(pal.partida_id)
            if not p or agora < p.data_hora:
                continue  # privacidade: só após o início
            m = helpers.nome_time(selecoes, p.mandante_id, p.slot_mandante)
            v = helpers.nome_time(selecoes, p.visitante_id, p.slot_visitante)
            pont = bet_repo.pontuacao(s, uid, p.id)
            linhas.append(
                f"- {m} {pal.gols_mandante}×{pal.gols_visitante} {v}"
                + (f" · **{pont.pontos_total} pt(s)**" if pont else "")
            )

    if linhas:
        st.markdown("\n".join(linhas))
    else:
        st.caption("Nenhum palpite visível ainda (jogos não iniciados).")
