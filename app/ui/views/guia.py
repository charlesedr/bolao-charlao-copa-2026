import streamlit as st

from app.ui import session as sess


def render() -> None:
    sess.current_user()
    st.title("📚 Guia rápido")
    st.caption("Tutorial passo a passo para você que está chegando agora. Leitura em ~3 min.")

    st.warning(
        "**Atenção ao prazo:** a **Aposta Final** (campeão/vice/3º/4º) "
        "**fecha em 11/06/2026 às 15:55 BRT**. Faça antes para concorrer a esses pontos."
    )

    # 1
    with st.container(border=True):
        st.subheader("1️⃣ Acessar e se cadastrar")
        st.markdown(
            "Pegue o link no grupo do WhatsApp. Abre direto no celular ou no computador. "
            "Se ainda não tem conta, clique em **Cadastrar** no menu lateral e preencha:"
        )
        st.code(
            """
┌─ Criar conta ─────────────────────────┐
│                                        │
│  Nome           [ Charles            ] │
│  Apelido        [ Nariz              ] │
│  E-mail         [ charles@email.com  ] │
│  Telefone/WPP   [ 11 98765-4321      ] │
│  Senha (≥ 6)    [ ••••••••           ] │
│                                        │
│  📱 telefone p/ grupo do WhatsApp      │
│                                        │
│  [          Cadastrar           ]      │
└────────────────────────────────────────┘
            """,
            language="text",
        )
        st.info(
            "💡 O **apelido** vira seu nome no ranking. O **telefone** é só para entrar no "
            "grupo do WhatsApp do bolão."
        )

    # 2
    with st.container(border=True):
        st.subheader("2️⃣ Aguardar a aprovação do admin")
        st.markdown("Logo depois de cadastrar, você verá:")
        st.code(
            """
┌──────────────────────────────────────┐
│  ⏳ Aguardando aprovação              │
│                                       │
│  Seu cadastro está aguardando        │
│  aprovação do administrador.          │
└──────────────────────────────────────┘
            """,
            language="text",
        )
        st.markdown("Avise o **admin** no grupo do WhatsApp para ele liberar mais rápido.")

    # 3
    with st.container(border=True):
        st.subheader("3️⃣ Palpitar os jogos da fase de grupos")
        st.markdown("No menu, clique em **⚽ Palpites**. Você verá os filtros no topo:")
        st.code(
            """
┌─ Data (opcional) ─┐  ┌─ Grupos / fase ─────┐
│   DD/MM/YYYY       │  │  escolha um ou mais │
└────────────────────┘  └─────────────────────┘
            """,
            language="text",
        )
        st.markdown(
            "E o **card de cada jogo** com indicador colorido do status do seu palpite "
            "(amarelo = ainda sem palpite, verde = já palpitou):"
        )
        st.code(
            """
┌─ Grupo C · 13/06 19:00 BRT · 🟢 Não iniciado ─┐
│                                                │
│  ⚠️  AINDA SEM PALPITE                         │
│                                                │
│  Brasil   ⚽   Marrocos                         │
│                                                │
│  Brasil          Marrocos                      │
│  [    2    ]     [    1    ]                   │
│                                                │
│  ☐ Marcar este jogo para salvar                │
└────────────────────────────────────────────────┘
            """,
            language="text",
        )
        st.markdown(
            "Edite os gols, **marque a checkbox** dos jogos que quer enviar, "
            "e use o botão no topo ou no rodapé:"
        )
        st.code("[💾 Salvar palpites marcados]", language="text")
        st.success(
            "✅ Quando salvar, o card vira verde: **✅ Já palpitado: 2 × 1**."
        )
        st.warning(
            "⚠️ **Se não marcar a checkbox, o palpite NÃO é salvo** — mesmo que você "
            "já tenha digitado os gols. Essa é a regra de \"não palpitou = não pontua\"."
        )

    # 4
    with st.container(border=True):
        st.subheader("4️⃣ Atenção à trava de 5 minutos")
        st.markdown(
            "Cada jogo fecha para palpite **5 minutos antes** de começar. "
            "Depois disso ele aparece trancado:"
        )
        st.code(
            """
┌─ Grupo C · 13/06 19:00 BRT · 🔴 Em andamento ─┐
│                                                │
│  Brasil   ⚽   Marrocos   🔒                    │
│                                                │
│  Seu palpite: 2 × 1                            │
└────────────────────────────────────────────────┘
            """,
            language="text",
        )
        st.info("💡 **Dica:** não deixe pra última hora. Palpite com antecedência.")

    # 5
    with st.container(border=True):
        st.subheader("5️⃣ Aposta Final — campeão, vice, 3º e 4º lugar")
        st.error(
            "🚨 **PRAZO:** a Aposta Final fecha **5 minutos antes do PRIMEIRO jogo da Copa** — "
            "**11/06/2026 às 15:55 BRT**. Depois desse momento, **não tem mais como palpitar**."
        )
        st.markdown("No menu, clique em **🏅 Aposta Final** e escolha 4 seleções **diferentes**:")
        st.code(
            """
┌─ 🏅 Aposta da Classificação Final ──────┐
│                                          │
│  🥇 Campeão                              │
│  [ Brasil                          ▾ ]   │
│                                          │
│  🥈 Vice-campeão                         │
│  [ Argentina                       ▾ ]   │
│                                          │
│  🥉 3º lugar                             │
│  [ França                          ▾ ]   │
│                                          │
│  4️⃣  4º lugar                            │
│  [ Espanha                         ▾ ]   │
│                                          │
│  [          Salvar aposta          ]     │
└──────────────────────────────────────────┘
            """,
            language="text",
        )
        st.markdown("Vale **+1 ponto por acerto** em cada posição (máx. 4 pts).")

    # 6
    with st.container(border=True):
        st.subheader("6️⃣ Acompanhar — Ranking, Minha Copa e Tela da Partida")
        st.markdown("**🏆 Ranking** — sua posição na disputa, atualiza sozinho:")
        st.code(
            """
┌─ 🏆 RANKING GERAL ───────────────────────┐
│  #   Participante         Pts  Plc  Res  │
│  1   Charles - Nariz      24    3    8   │
│  2   Felipe - corinthians 20    2    7   │
│  3   Lucas - lukas        18    1    8   │
└──────────────────────────────────────────┘
            """,
            language="text",
        )
        st.markdown(
            "**🌎 Minha Copa** — 2 abas: **Grupos** (sua simulação dos 12 grupos a partir "
            "dos seus palpites) e **Mata-mata** (prévia das suas 32avas, ou a chave real "
            "depois que a fase de grupos terminar)."
        )
        st.markdown(
            "**📋 Tela da Partida** — veja os palpites e os pontos de **todos** os participantes "
            "em cada jogo (os palpites alheios só aparecem **depois que o jogo começa**, "
            "para ninguém colar 😉)."
        )

    # 7
    with st.container(border=True):
        st.subheader("7️⃣ Mata-mata (a partir de 28/06)")
        st.markdown(
            "Quando o admin lançar os resultados oficiais da fase de grupos, os jogos do "
            "**mata-mata abrem para palpite** com os times reais que classificaram. Funciona "
            "igual à fase de grupos, com **uma novidade**: se você palpitar **empate nos 90 minutos**, "
            "precisa escolher **quem se classifica** nos pênaltis/prorrogação:"
        )
        st.code(
            """
┌─ Oitavas · 04/07 18:00 BRT ───────────┐
│ ⚠️  AINDA SEM PALPITE                  │
│                                        │
│ Brasil   ⚽   Argentina                 │
│                                        │
│ Brasil         Argentina               │
│ [    1    ]    [    1    ]             │
│                                        │
│ Empate nos 90 min:                     │
│ quem se classifica?                    │
│ (●) Brasil    ( ) Argentina            │
│                                        │
│ ☐ Marcar este jogo para salvar         │
└────────────────────────────────────────┘
            """,
            language="text",
        )
        st.info(
            "💡 No mata-mata o **placar conta só os 90 min**. Mas se você cravar **quem avança** "
            "(seja pela vitória direta ou pelo classificado em caso de empate), ganha "
            "**+1 ponto extra**. Total: até **6 pontos por jogo de mata-mata**."
        )

    # Dicas
    with st.container(border=True):
        st.subheader("💡 Dicas finais")
        st.markdown(
            """
- 📱 **Use o celular sem medo** — funciona certinho no browser do celular.
- 🔑 **Esqueceu a senha?** Fale com o admin que ele reseta.
- 🔄 **Atualizou o app e ficou estranho?** `Ctrl+Shift+R` no PC ou feche/reabra a aba no celular.
- 📋 Para **detalhes de regra/pontuação**, abra **❓ Como Funciona** no menu.
            """
        )

    st.divider()
    st.caption("Dúvidas que não estão aqui? Fale com o admin no grupo do WhatsApp. Bom bolão!")
