import streamlit as st

st.set_page_config(page_title="Configuração de câmbio", layout="wide")

st.title("Configuração manual de câmbio")
st.caption("Informe as cotações que serão usadas nos cálculos do sistema.")

# Valores padrão (caso não existam ainda)
if "usd_brl" not in st.session_state:
    st.session_state.usd_brl = 5.00
if "brl_ars" not in st.session_state:
    st.session_state.brl_ars = 200.0

with st.form("form_cambio"):
    usd_brl = st.number_input(
        "USD → BRL (1 USD em BRL)",
        min_value=0.0,
        value=float(st.session_state.usd_brl),
        step=0.01,
        format="%.4f",
    )
    brl_ars = st.number_input(
        "BRL → ARS (1 BRL em ARS)",
        min_value=0.0,
        value=float(st.session_state.brl_ars),
        step=0.1,
        format="%.4f",
    )

    submitted = st.form_submit_button("Salvar cotações")

if submitted:
    st.session_state.usd_brl = usd_brl
    st.session_state.brl_ars = brl_ars
    st.success("Cotações atualizadas com sucesso!")

st.write("Cotação atual em uso:")
st.metric("USD → BRL", f"{st.session_state.usd_brl:.4f}")
st.metric("BRL → ARS", f"{st.session_state.brl_ars:.4f}")
st.metric(
    "USD → ARS (derivada)",
    f"{(st.session_state.usd_brl / st.session_state.brl_ars):.4f}",
)
