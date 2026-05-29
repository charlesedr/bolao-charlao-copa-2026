"""Tema visual 'matchday' — claro e refinado, acento único verde (CSS estático)."""
import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,600;12..96,700&family=Archivo:wght@400;500;600;700&display=swap');

:root {
  --verde: #15633E;
  --verde-escuro: #0F4A2E;
  --papel: #F5F3EC;
  --tinta: #1B2420;
  --linha: #E4E0D4;
  --suave: #6B7269;
}

[data-testid="stAppViewContainer"] { background: var(--papel); }
[data-testid="stHeader"] { background: transparent; }

/* Tipografia: corpo Archivo, títulos Bricolage Grotesque */
html, body, .stMarkdown, p, label, input, button, select, textarea,
[data-testid="stWidgetLabel"] {
  font-family: 'Archivo', sans-serif;
  color: var(--tinta);
}
h1, h2, h3, h4 {
  font-family: 'Bricolage Grotesque', sans-serif !important;
  font-weight: 700;
  letter-spacing: -0.01em;
  color: var(--tinta);
}
h1 { color: var(--verde); }

/* Linha fina única no topo do conteúdo (sem cores berrantes) */
.block-container::before {
  content: "";
  display: block;
  height: 3px;
  width: 56px;
  background: var(--verde);
  border-radius: 3px;
  margin-bottom: 1.1rem;
}

/* Botões: verde sólido, sem brilho */
.stButton > button, .stFormSubmitButton > button {
  background: var(--verde);
  color: #FFFFFF;
  font-weight: 600;
  border: none;
  border-radius: 9px;
  transition: background .15s ease, transform .06s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
  background: var(--verde-escuro);
  color: #FFFFFF;
  transform: translateY(-1px);
}

/* Cards (container border=True): branco com borda neutra */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: #FFFFFF;
  border: 1px solid var(--linha) !important;
  border-radius: 14px;
  box-shadow: 0 1px 2px rgba(27,36,32,0.04);
}

/* Sidebar clara com borda sutil */
[data-testid="stSidebar"] {
  background: #FBFAF5;
  border-right: 1px solid var(--linha);
}

/* Inputs arredondados e neutros */
input, textarea, [data-baseweb="select"] > div, [data-baseweb="input"] {
  border-radius: 9px !important;
}

/* Tabelas: cabeçalho com leve tom verde */
[data-testid="stDataFrame"] thead tr th {
  background: rgba(21,99,62,0.07);
  color: var(--verde-escuro);
}

/* Abas: selecionada em verde */
[data-baseweb="tab-list"] button[aria-selected="true"] {
  color: var(--verde) !important;
}

/* Legendas em tom suave */
[data-testid="stCaptionContainer"], .stCaption { color: var(--suave) !important; }
</style>
"""


def aplicar_tema() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
