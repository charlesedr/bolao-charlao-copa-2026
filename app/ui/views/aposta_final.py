import streamlit as st
from sqlmodel import Session

from app.core.db import engine
from app.core.timezone import format_brt
from app.repositories import match_repo
from app.services import aposta_service
from app.ui import session as sess


def render() -> None:
    usuario = sess.current_user()
    st.title("🏅 Aposta da Classificação Final")
    st.caption(
        "Aposte em campeão, vice, 3º e 4º lugar — 1 ponto por acerto (máx. 4). "
        "**Trava 5 minutos antes do PRIMEIRO jogo da Copa** "
        "(11/jun/2026, 15:55 BRT). Depois disso, não há como palpitar."
    )

    with Session(engine) as s:
        aberta = aposta_service.aposta_aberta(s)
        aposta = aposta_service.get_aposta(s, usuario.id)
        completas, aprovados = aposta_service.contar_apostas(s)
        selecoes = sorted(match_repo.mapa_selecoes(s).values(), key=lambda x: x.nome_pt)

    if aprovados > 0:
        pct = (completas / aprovados) * 100
        st.caption(
            f"📊 **{completas} de {aprovados}** participantes "
            f"({pct:.0f}%) já fizeram a Aposta Final."
        )

    nomes = [x.nome_pt for x in selecoes]
    ids = [x.id for x in selecoes]
    nome_por_id = {x.id: x.nome_pt for x in selecoes}

    def _idx(sel_id: int | None) -> int:
        return ids.index(sel_id) if sel_id in ids else 0

    # Confirmação visual e persistente do estado atual da Aposta Final.
    aposta_completa = aposta is not None and all(
        getattr(aposta, campo, None) is not None
        for campo in ("campeao_id", "vice_id", "terceiro_id", "quarto_id")
    )
    if aposta_completa:
        atualizada_em = (
            f" · atualizada em {format_brt(aposta.updated_at, '%d/%m/%Y %H:%M')} BRT"
            if getattr(aposta, "updated_at", None)
            else ""
        )
        st.success(
            "✅ **Sua Aposta Final está registrada!**" + atualizada_em + "\n\n"
            f"- 🥇 **Campeão:** {nome_por_id.get(aposta.campeao_id, '—')}\n"
            f"- 🥈 **Vice-campeão:** {nome_por_id.get(aposta.vice_id, '—')}\n"
            f"- 🥉 **3º lugar:** {nome_por_id.get(aposta.terceiro_id, '—')}\n"
            f"- 4️⃣ **4º lugar:** {nome_por_id.get(aposta.quarto_id, '—')}\n\n"
            + (
                "Você pode editar abaixo até a trava."
                if aberta
                else "As apostas já estão encerradas — esta é a sua aposta final."
            )
        )
    elif aberta:
        st.info(
            "ℹ️ **Você ainda não fez sua Aposta Final.** "
            "Preencha os 4 campos abaixo e clique em **Salvar aposta**."
        )

    if not aberta:
        st.warning("⏰ As apostas estão encerradas.")

    with st.form("form_aposta"):
        c = st.selectbox("🥇 Campeão", nomes, index=_idx(aposta.campeao_id if aposta else None))
        v = st.selectbox("🥈 Vice-campeão", nomes, index=_idx(aposta.vice_id if aposta else None))
        t = st.selectbox("🥉 3º lugar", nomes, index=_idx(aposta.terceiro_id if aposta else None))
        q = st.selectbox("4️⃣ 4º lugar", nomes, index=_idx(aposta.quarto_id if aposta else None))
        salvar = st.form_submit_button(
            "Salvar aposta", use_container_width=True, disabled=not aberta
        )

    if salvar:
        with Session(engine) as s:
            ok, msg = aposta_service.salvar_aposta(
                s,
                usuario_id=usuario.id,
                campeao_id=ids[nomes.index(c)],
                vice_id=ids[nomes.index(v)],
                terceiro_id=ids[nomes.index(t)],
                quarto_id=ids[nomes.index(q)],
            )
        if ok:
            st.toast(msg, icon="✅")
            st.rerun()
        else:
            st.error(msg)

    if aposta and aposta.pontos_total:
        st.success(f"Sua aposta já pontuou: **{aposta.pontos_total}/4**")
