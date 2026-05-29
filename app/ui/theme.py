"""Tema visual 'estádio à noite' da Copa — injeta CSS (estático, sem dados do usuário)."""
import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Anton&family=Outfit:wght@300;400;500;600;700&display=swap');

:root {
  --verde: #0B6E4F;
  --verde-escuro: #07291d;
  --ouro: #E8B53D;
  --ouro-claro: #F6D67A;
  --texto: #F4F1E9;
}

/* Fundo: brilho dourado no topo + degradê de gramado noturno */
[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(1100px 520px at 50% -8%, rgba(232,181,61,0.12), transparent 60%),
    linear-gradient(180deg, #07291d 0%, #0a1f17 45%, #07120e 100%);
}
[data-testid="stHeader"] { background: transparent; }

/* Tipografia */
html, body, .stMarkdown, p, label, input, button, select, textarea,
[data-testid="stWidgetLabel"], [data-testid="stMetricValue"] {
  font-family: 'Outfit', sans-serif;
}
h1, h2, h3, h4 {
  font-family: 'Anton', sans-serif !important;
  letter-spacing: .6px;
  text-transform: uppercase;
  color: var(--texto);
}
h1 {
  color: var(--ouro);
  text-shadow: 0 2px 16px rgba(232,181,61,0.28);
}

/* Faixa decorativa verde-ouro no topo do conteúdo */
.block-container::before {
  content: "";
  display: block;
  height: 5px;
  width: 100%;
  background: linear-gradient(90deg, var(--verde), var(--ouro) 50%, var(--verde));
  border-radius: 6px;
  margin-bottom: 1rem;
  box-shadow: 0 2px 14px rgba(232,181,61,0.25);
}

/* Botões dourados */
.stButton > button, .stFormSubmitButton > button, [data-testid="stBaseButton-secondary"] {
  background: linear-gradient(180deg, var(--ouro-claro), var(--ouro));
  color: #2a1d00;
  font-weight: 700;
  border: none;
  border-radius: 10px;
  box-shadow: 0 4px 14px rgba(232,181,61,0.22);
  transition: transform .08s ease, box-shadow .2s ease;
}
.stButton > button:hover, .stFormSubmitButton > button:hover {
  transform: translateY(-1px);
  box-shadow: 0 7px 20px rgba(232,181,61,0.42);
  color: #000;
}

/* Cards com borda (container border=True) */
[data-testid="stVerticalBlockBorderWrapper"] {
  background: rgba(255,255,255,0.035);
  border: 1px solid rgba(232,181,61,0.18) !important;
  border-radius: 14px;
}

/* Sidebar estilo painel de estádio */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #07291d, #051611);
  border-right: 1px solid rgba(232,181,61,0.16);
}

/* Inputs / selects arredondados */
input, textarea, [data-baseweb="select"] > div, [data-baseweb="input"] {
  border-radius: 10px !important;
}

/* Tabelas (ranking) — cabeçalho dourado sutil */
[data-testid="stDataFrame"] thead tr th {
  background: rgba(232,181,61,0.10);
  color: var(--ouro-claro);
}

/* Abas */
[data-baseweb="tab-list"] button[aria-selected="true"] {
  color: var(--ouro) !important;
}
</style>
"""


def aplicar_tema() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
