import streamlit as st

from app.ui import session as sess


def render() -> None:
    sess.current_user()
    st.title("❓ Como Funciona")
    st.caption("Tudo o que você precisa saber para participar do Bolão Charlão Copa 2026.")

    st.header("🚀 Primeiros passos")
    st.markdown(
        """
1. **Cadastre-se** com nome, apelido, e-mail, telefone e senha.
2. Aguarde a **aprovação do administrador** (você recebe acesso assim que for aprovado).
3. Pronto! Você já pode **palpitar** nos jogos e acompanhar o **ranking**.
        """
    )

    st.header("⚽ Como palpitar")
    st.markdown(
        """
- Na aba **Palpites**, escolha um jogo e informe **quantos gols** cada seleção faz.
- Você pode **editar** seu palpite quantas vezes quiser, mas só **até 5 minutos antes** do início da partida. Depois disso, o palpite **trava**. 🔒
- Quem **não palpita** em um jogo fica com **0 ponto** naquele jogo.
- No **mata-mata**, se você palpitar **empate**, precisa escolher **quem se classifica**.
        """
    )

    st.header("🏅 Como funciona a pontuação")

    st.subheader("Fase de grupos — até 5 pontos por jogo")
    st.markdown(
        """
| O que você acerta | Pontos |
|---|---|
| Gols da seleção mandante | **+1** |
| Gols da seleção visitante | **+1** |
| Resultado (vitória de um, do outro, ou empate) | **+2** |
| Placar exato (bônus) | **+1** |
        """
    )
    st.markdown(
        """
**Exemplo:** resultado oficial **2 × 1**.
- Você palpitou **2 × 1** → acertou tudo = **5 pontos** 🎯
- Você palpitou **3 × 1** → acertou gols do visitante (+1) e o resultado (+2) = **3 pontos**
- Você palpitou **1 × 0** → acertou só o resultado (+2) = **2 pontos**
        """
    )

    st.subheader("Mata-mata — até 6 pontos por jogo")
    st.markdown(
        """
- Vale a **mesma regra dos grupos** (até 5 pontos), considerando **apenas os 90 minutos**
  (gols na prorrogação **não** contam para o placar).
- **+1 ponto** se você acertar **quem avança** para a próxima fase.

**Como o sistema sabe quem você acha que avança?**
- Se você palpitou a **vitória** de um time, é esse time que você indicou para passar.
- Se você palpitou **empate**, você escolhe na hora **quem se classifica** (nos pênaltis/prorrogação).

Esse ponto extra vale **independente de como o jogo foi decidido de verdade**
(90 minutos, prorrogação ou pênaltis): o que conta é se o time que **realmente avançou**
é o mesmo que **você indicou**.

**Exemplo:** o jogo terminou **1 × 1** e o time A passou nos pênaltis.
- Se você palpitou **vitória do A** (ex.: 2 × 1) → você indicou o A para avançar → ganha o **+1**.
- Se você palpitou **empate e escolheu o A** → também ganha o **+1**.
- Se você indicou o time B → não ganha o ponto de classificação.
        """
    )

    st.subheader("Aposta da classificação final — até 4 pontos")
    st.markdown(
        """
Na aba **Aposta Final**, você escolhe **campeão, vice, 3º e 4º lugar**.
Vale **+1 ponto por acerto** em cada posição. As apostas **travam 5 minutos antes
do jogo de disputa do 3º lugar**.
        """
    )

    st.header("🌎 Minha Copa")
    st.markdown(
        """
- **Aba Grupos:** mostra a classificação dos 12 grupos calculada **a partir dos seus palpites**
  (para simular um grupo, é preciso ter palpitado em todos os jogos dele).
- **Aba Mata-mata:** antes da fase de grupos acabar, mostra uma **prévia das suas 32avas**
  conforme suas previsões; depois, mostra a **chave real** com os times que se classificaram.
        """
    )

    st.header("📊 Acompanhando o bolão")
    st.markdown(
        """
- **Ranking:** classificação geral. Critérios de desempate, nesta ordem:
  **1)** pontos · **2)** placares exatos acertados · **3)** resultados acertados ·
  **4)** gols acertados (mandante + visitante). Se ainda assim houver empate total,
  os participantes **dividem a mesma posição**.
- **Tela da Partida:** veja o palpite e os pontos de **todos os participantes** em cada jogo
  (os palpites dos outros só aparecem **depois que o jogo começa**, para ninguém colar 😉).
- **Comparar** e **Perfil:** compare sua pontuação com a de outro participante e veja perfis.
        """
    )

    st.info("Dúvidas que não estão aqui? Fale com o administrador do bolão.")
