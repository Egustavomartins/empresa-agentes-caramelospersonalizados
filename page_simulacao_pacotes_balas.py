import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Simulação pacotes de balas", layout="wide")

# Tema escuro / textos brancos igual calculadora
st.markdown(
    """
    <style>
    .stApp {
        background-color: #020814;
        color: #FFFFFF;
    }
    .stMarkdown, .stText, .stCaption, .stMetric {
        color: #FFFFFF !important;
    }
    label, .stNumberInput label, .st-selectbox label {
        color: #FFFFFF !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

@st.cache_data(ttl=300)
def get_rates():
    resp = requests.get(
        "https://economia.awesomeapi.com.br/json/last/USD-BRL,BRL-ARS,USD-ARS"
    )
    data = resp.json()
    brl_ars = float(data["BRLARS"]["bid"])  # 1 BRL em ARS
    return brl_ars

brl_ars = get_rates()

st.title("Simulação de combinações de pacotes de balas")
st.caption("Ajuste os pacotes A e B e veja o faturamento e a quantidade total de balas.")

card_style = (
    "background-color:#041728;"
    "padding:18px 20px;"
    "border-radius:12px;"
    "border:1px solid #123456;"
)

# -----------------------------
# Inputs
# -----------------------------
col1, col2, col3 = st.columns(3)

with col1:
    qtd_a = st.number_input("Qtd balas Pacote A", min_value=1, value=1000)
    preco_a = st.number_input("Preço Pacote A (ARS)", min_value=0, value=120000)
with col2:
    qtd_b = st.number_input("Qtd balas Pacote B", min_value=1, value=500)
    preco_b = st.number_input("Preço Pacote B (ARS)", min_value=0, value=75000)
with col3:
    meta_faturamento = st.number_input(
        "Meta de faturamento (ARS)",
        min_value=0,
        value=6720000,
    )

st.markdown("---")

# -----------------------------
# Cards de parâmetros (A, B, Meta) com valor em ARS e BRL
# -----------------------------
st.markdown("### Parâmetros atuais")

col_p1, col_p2, col_p3 = st.columns(3)

meta_em_brl = meta_faturamento / brl_ars if brl_ars > 0 else 0
preco_a_em_brl = preco_a / brl_ars if brl_ars > 0 else 0
preco_b_em_brl = preco_b / brl_ars if brl_ars > 0 else 0

with col_p1:
    st.markdown(
        f"""
        <div style="{card_style}">
            <div style="color:#8FA3BF; font-size:11px; text-transform:uppercase;">
                PACOTE A
            </div>
            <div style="color:#FFFFFF; font-size:18px; font-weight:700; margin-top:4px;">
                {qtd_a} balas
            </div>
            <div style="color:#8FA3BF; font-size:13px; margin-top:2px;">
                {preco_a:,} ARS
            </div>
            <div style="color:#8FA3BF; font-size:13px; margin-top:2px;">
                ≈ R$ {preco_a_em_brl:,.2f}
            </div>
        </div>
        """.replace(",", "X").replace(".", ",").replace("X", "."),
        unsafe_allow_html=True,
    )

with col_p2:
    st.markdown(
        f"""
        <div style="{card_style}">
            <div style="color:#8FA3BF; font-size:11px; text-transform:uppercase;">
                PACOTE B
            </div>
            <div style="color:#FFFFFF; font-size:18px; font-weight:700; margin-top:4px;">
                {qtd_b} balas
            </div>
            <div style="color:#8FA3BF; font-size:13px; margin-top:2px;">
                {preco_b:,} ARS
            </div>
            <div style="color:#8FA3BF; font-size:13px; margin-top:2px;">
                ≈ R$ {preco_b_em_brl:,.2f}
            </div>
        </div>
        """.replace(",", "X").replace(".", ",").replace("X", "."),
        unsafe_allow_html=True,
    )

with col_p3:
    st.markdown(
        f"""
        <div style="{card_style}">
            <div style="color:#8FA3BF; font-size:11px; text-transform:uppercase;">
                META DE FATURAMENTO
            </div>
            <div style="color:#FFFFFF; font-size:18px; font-weight:700; margin-top:4px;">
                {meta_faturamento:,} ARS
            </div>
            <div style="color:#8FA3BF; font-size:13px; margin-top:6px;">
                ≈ R$ {meta_em_brl:,.2f}
            </div>
        </div>
        """.replace(",", "X").replace(".", ",").replace("X", "."),
        unsafe_allow_html=True,
    )

st.markdown("---")

# -----------------------------
# Tabela de combinações
# -----------------------------
st.markdown("### Combinações de pacotes A e B")

combos_base = [
    {"Pacotes A": 56, "Pacotes B": 0},
    {"Pacotes A": 40, "Pacotes B": 24},
    {"Pacotes A": 30, "Pacotes B": 48},
    {"Pacotes A": 20, "Pacotes B": 64},
    {"Pacotes A": 10, "Pacotes B": 80},
    {"Pacotes A": 0,  "Pacotes B": 90},
]

linhas = []
for c in combos_base:
    pa = c["Pacotes A"]
    pb = c["Pacotes B"]
    faturamento = pa * preco_a + pb * preco_b
    balas_totais = pa * qtd_a + pb * qtd_b
    faturamento_em_brl = faturamento / brl_ars if brl_ars > 0 else 0

    linhas.append(
        {
            "Pacotes A": pa,
            "Pacotes B": pb,
            "Faturamento total (ARS)": faturamento,
            "Faturamento total (BRL)": round(faturamento_em_brl, 2),
            "Balas totais": balas_totais,
        }
    )

df = pd.DataFrame(linhas)

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
)

