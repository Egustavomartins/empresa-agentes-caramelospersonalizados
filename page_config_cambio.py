import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Configuração de câmbio", layout="wide")

st.title("Configuração manual de câmbio")
st.caption("Informe as cotações que serão usadas nos cálculos do sistema.")

# Valores padrão (caso não existam ainda)
if "usd_brl" not in st.session_state:
    st.session_state.usd_brl = 5.00
if "brl_ars" not in st.session_state:
    st.session_state.brl_ars = 200.0

# Frame do Google com cotação embutida
st.markdown("### Consultar cotação atual")

# URL do Google com busca já pronta para "usd to brl" e "brl to ars"
# Você pode escolher qual mostra, ou colocar os dois em abas
tab1, tab2 = st.tabs(["USD → BRL", "BRL → ARS"])

with tab1:
    components.iframe(
        "https://www.google.com/search?igu=1&q=usd+to+brl",
        height=400,
        scrolling=True,
    )

with tab2:
    components.iframe(
        "https://www.google.com/search?igu=1&q=brl+to+ars",
        height=400,
        scrolling=True,
    )

st.markdown("---")

# Inputs sempre começam com o valor atual em uso
usd_brl_input = st.number_input(
    "USD → BRL (1 USD em BRL)",
    min_value=0.0,
    value=float(st.session_state.usd_brl),
    step=0.01,
    format="%.4f",
    key="usd_brl_input",
)
brl_ars_input = st.number_input(
    "BRL → ARS (1 BRL em ARS)",
    min_value=0.0,
    value=float(st.session_state.brl_ars),
    step=0.1,
    format="%.4f",
    key="brl_ars_input",
)

def salvar_cotacoes():
    st.session_state.usd_brl = st.session_state.usd_brl_input
    st.session_state.brl_ars = st.session_state.brl_ars_input

# Botão pode ser clicado quantas vezes quiser
st.button("Salvar cotações", on_click=salvar_cotacoes)

st.markdown("---")

st.write("Cotação atual em uso:")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("USD → BRL", f"{st.session_state.usd_brl:.4f}")
with col2:
    st.metric("BRL → ARS", f"{st.session_state.brl_ars:.4f}")
with col3:
    st.metric(
        "USD → ARS (derivada)",
        f"{(st.session_state.usd_brl * st.session_state.brl_ars):.4f}",
    )
