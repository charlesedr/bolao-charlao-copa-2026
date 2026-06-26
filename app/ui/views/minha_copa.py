import pandas as pd
import streamlit as st
from sqlmodel import Session

from app.core.db import engine
from app.domain.enums import FasePartida
from app.repositories import bet_repo, match_repo
from app.services import bracket_sim_service, simulation_service
from app.ui import helpers
from app.ui import session as sess

FASES_MATA = [
    FasePartida.R32,
    FasePartida.OITAVAS,
    FasePartida.QUARTAS,
    FasePartida.SEMIFINAL,
    FasePartida.DISPUTA_3O,
    FasePartida.FINAL,
]

LABEL_FASE_SIM = {
    FasePartida.R32: "32avos",
    FasePartida.OITAVAS: "Oitavas",
    FasePartida.QUARTAS: "Quartas",
    FasePartida.SEMIFINAL: "Semifinal",
    FasePartida.FINAL: "Final",
    FasePartida.DISPUTA_3O: "Disputa de 3º",
}


def _df_classificacao(info: dict, selecoes: dict) -> pd.DataFrame:
    linhas = []
    for i, linha in enumerate(info["linhas"], start=1):
        marca = "✅" if i <= 2 else ("🟡" if i == 3 else "")
        nome_sel = selecoes[linha.selecao_id].nome_pt if linha.selecao_id in selecoes else "?"
        linhas.append(
            {
                "#": i,
                "Seleção": f"{marca} {nome_sel}".strip(),
                "P": linha.pontos,
                "J": linha.jogos,
                "V": linha.vitorias,
                "SG": linha.saldo,
                "GP": linha.gols_pro,
            }
        )
    return pd.DataFrame(linhas)


def _render_tabela_classificacao(info: dict, selecoes: dict, msg_incompleto: str) -> None:
    if not info["completo"]:
        st.caption(msg_incompleto)
        return
    st.dataframe(_df_classificacao(info, selecoes), hide_index=True, use_container_width=True)


def _render_grupos(usuario_id: int) -> None:
    st.caption(
        "À esquerda: seus palpites puros. À direita: resultados oficiais já finalizados "
        "+ seus palpites nos jogos restantes."
    )
    with Session(engine) as s:
        resultado, selecoes = simulation_service.simular_grupos(s, usuario_id)
        hibrido, _ = simulation_service.simular_grupos_hibrido(s, usuario_id)

    for nome, info in resultado.items():
        st.subheader(f"Grupo {nome}")
        st.markdown("**Seus palpites**")
        _render_tabela_classificacao(
            info,
            selecoes,
            (
                "⚠️ Palpite em todos os jogos do grupo para simular "
                f"({info['palpitados']}/{info['total_jogos']})."
            ),
        )

        st.markdown("**Real + projeção**")
        info_hibrido = hibrido.get(nome)
        if info_hibrido is None:
            st.caption("⚠️ Grupo sem dados para projetar.")
            continue
        if info_hibrido["completo"]:
            st.caption(
                f"Oficiais: {info_hibrido['oficiais']} · "
                f"Projetados: {info_hibrido['projetados']}"
            )
        _render_tabela_classificacao(
            info_hibrido,
            selecoes,
            (
                "⚠️ Faltam palpites nos jogos sem resultado oficial "
                f"({info_hibrido['pendentes']} pendente(s))."
            ),
        )

    st.caption("✅ classificados (1º e 2º) · 🟡 3º colocado (pode avançar como um dos 8 melhores)")


def _render_bracket_real(s: Session, usuario_id: int) -> None:
    st.caption("Chave **real** com os times classificados + os seus palpites.")
    selecoes = match_repo.mapa_selecoes(s)
    for fase in FASES_MATA:
        jogos = match_repo.listar(s, fase)
        if not jogos:
            continue
        st.subheader(helpers.FASE_LABEL.get(fase, fase))
        for p in jogos:
            m = helpers.nome_time(selecoes, p.mandante_id, p.slot_mandante)
            v = helpers.nome_time(selecoes, p.visitante_id, p.slot_visitante)
            texto = f"**{m}** x **{v}**"
            if p.placar_mandante is not None:
                texto += f" — oficial {p.placar_mandante}×{p.placar_visitante}"
            palpite = bet_repo.get(s, usuario_id, p.id)
            if palpite:
                texto += f" · seu palpite {palpite.gols_mandante}×{palpite.gols_visitante}"
            st.write(texto)


def _render_fase_sim(
    items: list[dict],
    fase: str,
    liberada: bool,
    selecoes: dict,
    usuario_id: int,
) -> None:
    label = LABEL_FASE_SIM.get(fase, fase)
    n_confrontos = len(items)
    n_palpitados = sum(
        1 for it in items if it["palpite"] is not None and not it["dependencia_pendente"]
    )
    titulo = f"▼ {label} · {n_palpitados}/{n_confrontos}"

    with st.expander(titulo, expanded=liberada and n_palpitados < n_confrontos):
        if not liberada:
            st.info(f"🔒 Complete a fase anterior para liberar **{label}**.")
            return

        pendentes = [it for it in items if it["dependencia_pendente"]]
        prontos = [it for it in items if not it["dependencia_pendente"]]

        for it in pendentes:
            st.warning(
                f"⚠️ Jogo #{it['codigo']}: aguardando palpite dos confrontos anteriores."
            )

        if not prontos:
            return

        # Tudo dentro de st.form: widgets NÃO disparam rerun a cada interação.
        # Só o form_submit_button gera UM rerun (no clique em Salvar).
        with st.form(key=f"sim_form_{fase}", clear_on_submit=False):
            for it in prontos:
                partida_id = it["partida_id"]
                codigo = it["codigo"]
                palpite = it["palpite"]
                mandante_id = it["mandante_id"]
                visitante_id = it["visitante_id"]
                nome_m = selecoes[mandante_id].nome_pt
                nome_v = selecoes[visitante_id].nome_pt

                with st.container(border=True):
                    cab = f"**#{codigo}** · {nome_m} 🌍 {nome_v}"
                    if palpite is not None:
                        venc_nome = (
                            nome_m if palpite.vencedor_id == mandante_id else nome_v
                        )
                        cab += (
                            f" — ✅ {venc_nome} venceu "
                            f"{palpite.placar_vencedor}×{palpite.placar_perdedor}"
                        )
                    st.markdown(cab)

                    if palpite is not None and palpite.vencedor_id == mandante_id:
                        default_m, default_v = palpite.placar_vencedor, palpite.placar_perdedor
                        default_venc_idx = 0
                    elif palpite is not None and palpite.vencedor_id == visitante_id:
                        default_m, default_v = palpite.placar_perdedor, palpite.placar_vencedor
                        default_venc_idx = 1
                    else:
                        default_m, default_v = 0, 0
                        default_venc_idx = 0

                    col1, col2 = st.columns(2)
                    with col1:
                        st.number_input(
                            nome_m,
                            key=f"sim_m_{partida_id}",
                            min_value=0, max_value=30, step=1,
                            value=default_m,
                        )
                    with col2:
                        st.number_input(
                            nome_v,
                            key=f"sim_v_{partida_id}",
                            min_value=0, max_value=30, step=1,
                            value=default_v,
                        )

                    # Radio sempre presente (forms não reagem a mudanças de valor):
                    # só é usado quando o placar empata.
                    st.radio(
                        "Em caso de empate, quem se classifica?",
                        [nome_m, nome_v],
                        index=default_venc_idx,
                        key=f"sim_venc_{partida_id}",
                        horizontal=True,
                    )

                    st.checkbox(
                        "Marcar este confronto para salvar",
                        key=f"sim_inc_{partida_id}",
                        value=(palpite is not None),
                    )

            submitted = st.form_submit_button(
                f"💾 Salvar palpites marcados de {label}",
                use_container_width=True,
                type="primary",
            )

        if submitted:
            salvos, erros = 0, 0
            with Session(engine) as s:
                for it in prontos:
                    pid = it["partida_id"]
                    if not st.session_state.get(f"sim_inc_{pid}"):
                        continue
                    gm = int(st.session_state.get(f"sim_m_{pid}", 0))
                    gv = int(st.session_state.get(f"sim_v_{pid}", 0))
                    nome_m = selecoes[it["mandante_id"]].nome_pt
                    if gm == gv:
                        venc_nome = st.session_state.get(f"sim_venc_{pid}", nome_m)
                        venc_id = (
                            it["mandante_id"] if venc_nome == nome_m else it["visitante_id"]
                        )
                    else:
                        venc_id = it["mandante_id"] if gm > gv else it["visitante_id"]
                    ok, _ = bracket_sim_service.salvar(
                        s,
                        usuario_id=usuario_id,
                        partida_id=pid,
                        vencedor_id=venc_id,
                        placar_vencedor=max(gm, gv),
                        placar_perdedor=min(gm, gv),
                    )
                    if ok:
                        salvos += 1
                    else:
                        erros += 1
            if salvos:
                st.toast(f"✅ {salvos} palpite(s) simulado(s) salvo(s).")
                st.rerun()
            elif erros:
                st.error(f"{erros} erro(s) ao salvar.")
            else:
                st.toast("⚠️ Nenhum confronto marcado para salvar.")


def _render_bracket_simulado(usuario_id: int) -> None:
    with Session(engine) as s:
        chave = bracket_sim_service.montar_chave(s, usuario_id)
        selecoes = match_repo.mapa_selecoes(s)

    if chave["status"] == "incompleto":
        st.info(chave["msg"])
        return

    st.caption(
        "ℹ️ Esta é a **sua simulação** do mata-mata, construída em cima dos seus "
        "resultados oficiais dos grupos + seus palpites nos jogos restantes. "
        "**Não vale ponto no bolão** — é só para você cravar como acha que a Copa vai acabar."
    )

    if chave["inconsistencias"]:
        st.warning(
            "⚠️ Sua simulação está desatualizada (você mudou palpites de grupos "
            "ou a classificação real/projetada mudou). Veja os pontos abaixo e, se quiser, "
            "clique em **Reiniciar simulação**:\n\n- "
            + "\n- ".join(chave["inconsistencias"])
        )

    if chave["campeao_id"]:
        st.success(
            f"🏆 **Seu campeão previsto:** {selecoes[chave['campeao_id']].nome_pt}"
        )

    if st.button("🔄 Reiniciar minha simulação do mata-mata", type="secondary"):
        with Session(engine) as s:
            n = bracket_sim_service.resetar(s, usuario_id)
        st.toast(f"Simulação reiniciada ({n} palpite(s) removido(s)).")
        st.rerun()

    fases = chave["fases"]
    sequencial = [
        FasePartida.R32,
        FasePartida.OITAVAS,
        FasePartida.QUARTAS,
        FasePartida.SEMIFINAL,
    ]
    fase_anterior_ok = True
    for fase in sequencial:
        items = fases.get(fase, [])
        _render_fase_sim(items, fase, fase_anterior_ok, selecoes, usuario_id)
        fase_anterior_ok = bracket_sim_service.fase_completa(items)

    sf_ok = fase_anterior_ok
    for fase in (FasePartida.FINAL, FasePartida.DISPUTA_3O):
        items = fases.get(fase, [])
        _render_fase_sim(items, fase, sf_ok, selecoes, usuario_id)


def _render_mata(usuario_id: int) -> None:
    with Session(engine) as s:
        grupos_real = match_repo.listar(s, FasePartida.GRUPOS)
        real_finalizado = bool(grupos_real) and all(
            p.placar_mandante is not None for p in grupos_real
        )
    if real_finalizado:
        with Session(engine) as s:
            _render_bracket_real(s, usuario_id)
        return
    _render_bracket_simulado(usuario_id)


def render() -> None:
    usuario = sess.current_user()
    st.title("🌎 Minha Copa")
    aba_grupos, aba_mata = st.tabs(["🏆 Grupos", "🔥 Mata-mata"])
    with aba_grupos:
        _render_grupos(usuario.id)
    with aba_mata:
        _render_mata(usuario.id)
