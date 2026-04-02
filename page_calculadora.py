import streamlit as st
import requests

st.set_page_config(page_title="Calculadora cambial", layout="wide")

# Tema escuro / textos brancos (como nas outras páginas)
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

st.title("Calculadora cambial")
st.caption("Conversao rapida entre reais, dolares e pesos, usando cotacoes em tempo real.")

@st.cache_data(ttl=300)
def get_rates():
    resp = requests.get(
        "https://economia.awesomeapi.com.br/json/last/USD-BRL,BRL-ARS,USD-ARS"
    )
    data = resp.json()
    usd_brl = float(data["USDBRL"]["bid"])   # 1 USD em BRL
    brl_ars = float(data["BRLARS"]["bid"])  # 1 BRL em ARS
    usd_ars = float(data["USDARS"]["bid"])  # 1 USD em ARS
    return usd_brl, brl_ars, usd_ars

usd_brl, brl_ars, usd_ars = get_rates()

card_style = (
    "background-color:#041728;"
    "padding:18px 20px;"
    "border-radius:12px;"
    "border:1px solid #123456;"
)

# ---------------------------------------------------------
# Cards com taxas atuais
# ---------------------------------------------------------
st.markdown("### Taxas de cambio atuais")

usd_brl_str = f"{usd_brl:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")
brl_ars_str = f"{brl_ars:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")
usd_ars_str = f"{usd_ars:,.4f}".replace(",", "X").replace(".", ",").replace("X", ".")

col_t1, col_t2, col_t3 = st.columns(3)

with col_t1:
    st.markdown(
        f"""
        <div style="{card_style}">
            <div style="color:#8FA3BF; font-size:12px; text-transform:uppercase;">
                1 USD EM BRL
            </div>
            <div style="color:#FFFFFF; font-size:22px; font-weight:700; margin-top:4px;">
                R$ {usd_brl_str}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_t2:
    st.markdown(
        f"""
        <div style="{card_style}">
            <div style="color:#8FA3BF; font-size:12px; text-transform:uppercase;">
                1 BRL EM ARS
            </div>
            <div style="color:#FFFFFF; font-size:22px; font-weight:700; margin-top:4px;">
                $ {brl_ars_str}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col_t3:
    st.markdown(
        f"""
        <div style="{card_style}">
            <div style="color:#8FA3BF; font-size:12px; text-transform:uppercase;">
                1 USD EM ARS
            </div>
            <div style="color:#FFFFFF; font-size:22px; font-weight:700; margin-top:4px;">
                $ {usd_ars_str}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# ---------------------------------------------------------
# Linha 1: BRL -> USD / ARS
# ---------------------------------------------------------
st.markdown("### Converter de reais para dolar e pesos")

col_in_brl, col_out_brl = st.columns([1, 2])

with col_in_brl:
    valor_brl = st.number_input(
        "Valor em reais (BRL)",
        min_value=0.0,
        value=0.0,
        step=10.0,
    )

brl_to_usd = valor_brl / usd_brl if usd_brl > 0 else 0.0
brl_to_ars = valor_brl * brl_ars

brl_to_usd_str = f"{brl_to_usd:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
brl_to_ars_str = f"{brl_to_ars:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

with col_out_brl:
    st.markdown(
        f"""
        <div style="display:flex; gap:16px;">
            <div style="{card_style}; flex:1;">
                <div style="color:#8FA3BF; font-size:11px; text-transform:uppercase;">
                    EM DOLAR (USD)
                </div>
                <div style="color:#FFFFFF; font-size:20px; font-weight:700; margin-top:4px;">
                    {brl_to_usd_str}
                </div>
            </div>
            <div style="{card_style}; flex:1;">
                <div style="color:#8FA3BF; font-size:11px; text-transform:uppercase;">
                    EM PESOS (ARS)
                </div>
                <div style="color:#FFFFFF; font-size:20px; font-weight:700; margin-top:4px;">
                    {brl_to_ars_str}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# ---------------------------------------------------------
# Linha 2: ARS -> USD / BRL
# ---------------------------------------------------------
st.markdown("### Converter de pesos para dolar e reais")

col_in_ars, col_out_ars = st.columns([1, 2])

with col_in_ars:
    valor_ars = st.number_input(
        "Valor em pesos (ARS)",
        min_value=0.0,
        value=0.0,
        step=100.0,
    )

ars_to_brl = valor_ars / brl_ars if brl_ars > 0 else 0.0
ars_to_usd = valor_ars / usd_ars if usd_ars > 0 else 0.0

ars_to_brl_str = f"{ars_to_brl:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
ars_to_usd_str = f"{ars_to_usd:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

with col_out_ars:
    st.markdown(
        f"""
        <div style="display:flex; gap:16px;">
            <div style="{card_style}; flex:1;">
                <div style="color:#8FA3BF; font-size:11px; text-transform:uppercase;">
                    EM DOLAR (USD)
                </div>
                <div style="color:#FFFFFF; font-size:20px; font-weight:700; margin-top:4px;">
                    {ars_to_usd_str}
                </div>
            </div>
            <div style="{card_style}; flex:1;">
                <div style="color:#8FA3BF; font-size:11px; text-transform:uppercase;">
                    EM REAIS (BRL)
                </div>
                <div style="color:#FFFFFF; font-size:20px; font-weight:700; margin-top:4px;">
                    {ars_to_brl_str}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")

# ---------------------------------------------------------
# Linha 3: USD -> BRL / ARS
# ---------------------------------------------------------
st.markdown("### Converter de dolar para reais e pesos")

col_in_usd, col_out_usd = st.columns([1, 2])

with col_in_usd:
    valor_usd = st.number_input(
        "Valor em dolar (USD)",
        min_value=0.0,
        value=0.0,
        step=10.0,
    )

usd_to_brl = valor_usd * usd_brl
usd_to_ars = valor_usd * usd_ars

usd_to_brl_str = f"{usd_to_brl:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
usd_to_ars_str = f"{usd_to_ars:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

with col_out_usd:
    st.markdown(
        f"""
        <div style="display:flex; gap:16px;">
            <div style="{card_style}; flex:1;">
                <div style="color:#8FA3BF; font-size:11px; text-transform:uppercase;">
                    EM REAIS (BRL)
                </div>
                <div style="color:#FFFFFF; font-size:20px; font-weight:700; margin-top:4px;">
                    {usd_to_brl_str}
                </div>
            </div>
            <div style="{card_style}; flex:1;">
                <div style="color:#8FA3BF; font-size:11px; text-transform:uppercase;">
                    EM PESOS (ARS)
                </div>
                <div style="color:#FFFFFF; font-size:20px; font-weight:700; margin-top:4px;">
                    {usd_to_ars_str}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
