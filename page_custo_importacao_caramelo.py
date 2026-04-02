import streamlit as st
import requests

st.set_page_config(page_title="Custo de importacao", layout="wide")

# Fundo escuro + textos/labels brancos
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

st.title("Custo de importacao dos caramelos")
st.caption("Calculos considerando lote padrao de 2000 kg de caramelos.")

@st.cache_data(ttl=300)
def get_rates():
    resp = requests.get(
        "https://economia.awesomeapi.com.br/json/last/USD-BRL,BRL-ARS,USD-ARS"
    )
    data = resp.json()

    usd_brl = float(data["USDBRL"]["bid"])      # 1 USD em BRL
    brl_ars = float(data["BRLARS"]["bid"])     # 1 BRL em ARS
    usd_ars = float(data["USDARS"]["bid"])     # 1 USD em ARS

    return usd_brl, brl_ars, usd_ars

usd_brl, brl_ars, usd_ars = get_rates()

# ---------------------------------------------------------
# Parametros basicos e taxas de cambio
# ---------------------------------------------------------
st.markdown("### Parametros basicos e taxas de cambio")

col_tc1, col_tc2, col_tc3 = st.columns(3)

with col_tc1:
    taxa_brl_usd = st.number_input(
        "Taxa BRL -> USD (quantos reais valem 1 dolar)",
        min_value=0.0,
        value=usd_brl,
        step=0.01,
    )

with col_tc2:
    taxa_brl_ars = st.number_input(
        "Taxa BRL -> ARS (quantos pesos valem 1 real)",
        min_value=0.0,
        value=brl_ars,
        step=1.0,
    )

with col_tc3:
    taxa_usd_ars = st.number_input(
        "Taxa USD -> ARS (quantos pesos valem 1 dolar)",
        min_value=0.0,
        value=usd_ars,
        step=10.0,
    )

# ---------------------------------------------------------
# Valores da compra e fretes
# ---------------------------------------------------------
st.markdown("### Valores da compra e fretes")

col_v1, col_v2 = st.columns(2)

with col_v1:
    valor_produto_brl = st.number_input(
        "Valor dos produtos (reais) - lote 2000 kg",
        min_value=0.0,
        value=14540.0,
        step=500.0,
    )

with col_v2:
    frete_foz_brl = st.number_input(
        "Frete ate Foz do Iguacu (reais)",
        min_value=0.0,
        value=0.0,
        step=100.0,
    )

valor_compra_brl = valor_produto_brl + frete_foz_brl
valor_compra_usd = valor_compra_brl / taxa_brl_usd if taxa_brl_usd > 0 else 0.0

total_str = f"{valor_compra_brl:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
prod_str = f"{valor_produto_brl:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
frete_str = f"{frete_foz_brl:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

st.write(
    f"Total produtos + frete ate Foz: **R$ {total_str}** "
    f"(produtos: R$ {prod_str} + frete: R$ {frete_str})"
)

col_f1, col_f2 = st.columns(2)

with col_f1:
    frete_foz_puerto_usd = st.number_input(
        "Frete Foz -> Puerto Iguacu (USD)",
        min_value=0.0,
        value=200.0,
        step=10.0,
    )

with col_f2:
    frete_corrientes_usd = st.number_input(
        "Frete Puerto Iguacu -> Corrientes (USD)",
        min_value=0.0,
        value=200.0,
        step=10.0,
    )

seguro_usd = st.number_input(
    "Seguro internacional (USD)",
    min_value=0.0,
    value=29.99,
    step=5.0,
)

valor_aduaneiro_usd = st.number_input(
    "Valor aduaneiro (USD)",
    min_value=0.0,
    value=150.0,
    step=10.0,
    help="Custos de aduana fixos (ex.: 150 USD).",
)

# ---------------------------------------------------------
# Calculo em USD
# ---------------------------------------------------------
st.markdown("### Calculo em USD")

cip_foz_usd = valor_compra_usd + seguro_usd

total_corrientes_usd = (
    cip_foz_usd
    + frete_foz_puerto_usd
    + frete_corrientes_usd
    + valor_aduaneiro_usd
)

st.write(
    f"Valor da compra em USD (aprox.): **{valor_compra_usd:,.2f} USD**"
    .replace(",", "X").replace(".", ",").replace("X", ".")
)
st.write(
    f"CIP Foz (compra + seguro): **{cip_foz_usd:,.2f} USD**"
    .replace(",", "X").replace(".", ",").replace("X", ".")
)
st.write(
    f"Total ate Corrientes (CIP Foz + fretes argentinos + valor aduaneiro): "
    f"**{total_corrientes_usd:,.2f} USD**"
    .replace(",", "X").replace(".", ",").replace("X", ".")
)

# ---------------------------------------------------------
# Flag MiPyME (com ou sem percepções extra)
# ---------------------------------------------------------
st.markdown("### Regime fiscal da importacao")

col_flag1, col_flag2 = st.columns(2)
with col_flag1:
    mipymE_com_exclusao = st.checkbox(
        "Empresa/importacao COM exclusao MiPyME (sem IVA adicional 20% e Ganancias 6%)",
        value=True,
        help="Quando marcado, considera que ha Certificado MiPyME/exclusao e nao calcula percepcoes extras.",
    )

with col_flag2:
    st.caption(
        "Se desmarcar, o sistema simula percepcoes de IVA adicional 20% (credito) e Ganancias 6% (antecipacao)."
    )

# ---------------------------------------------------------
# Impostos em USD
# ---------------------------------------------------------
st.markdown("### Impostos em USD")

aliquota_iva = st.number_input(
    "IVA sobre importacao (% sobre CIP Foz)",
    min_value=0.0,
    max_value=30.0,
    value=21.0,
    step=0.5,
)

aliquota_prov = st.number_input(
    "Aliquota provincial (% sobre CIP Foz)",
    min_value=0.0,
    max_value=10.0,
    value=2.5,
    step=0.1,
)

valor_sim_usd = st.number_input(
    "SIM (Sistema de Importacion de Mercaderias) - USD",
    min_value=0.0,
    value=10.0,
    step=5.0,
    help="Taxa SIM cobrada na importacao (valor padrao 10 USD).",
)

# INAL 0,5% sobre o valor da nota (usando CIP Foz como base)
aliquota_inal = st.number_input(
    "INAL (% sobre valor da nota/CIP Foz)",
    min_value=0.0,
    max_value=5.0,
    value=0.5,
    step=0.1,
    help="Taxa do Instituto Nacional de Alimentos (padrao 0,5% sobre o valor da nota).",
)

# Percepcoes adicionais (apenas se nao houver exclusao MiPyME)
if mipymE_com_exclusao:
    aliquota_iva_adic = 0.0
    aliquota_ganancias = 0.0
else:
    aliquota_iva_adic = st.number_input(
        "IVA adicional (% sobre base da importacao)",
        min_value=0.0,
        max_value=30.0,
        value=20.0,
        step=0.5,
        help="Percepcao de IVA adicional na importacao (ex.: 20%).",
    )
    aliquota_ganancias = st.number_input(
        "Ganancias (% sobre base da importacao)",
        min_value=0.0,
        max_value=10.0,
        value=6.0,
        step=0.5,
        help="Percepcao de Impuesto a las Ganancias na importacao (ex.: 6%).",
    )

# Base para todas as percepcoes: CIP Foz
base_percep_usd = cip_foz_usd

iva_usd = base_percep_usd * (aliquota_iva / 100.0)
imposto_prov_usd = base_percep_usd * (aliquota_prov / 100.0)
inal_usd = base_percep_usd * (aliquota_inal / 100.0)
iva_adicional_usd = base_percep_usd * (aliquota_iva_adic / 100.0)
ganancias_usd = base_percep_usd * (aliquota_ganancias / 100.0)

# Separacao: nao recuperaveis x recuperaveis / antecipacao
impostos_nao_recuperaveis_usd = imposto_prov_usd + valor_sim_usd + inal_usd
impostos_recuperaveis_usd = iva_usd + iva_adicional_usd
impostos_antecipados_ganancias_usd = ganancias_usd

st.write(
    f"IVA ({aliquota_iva:.1f}% sobre CIP Foz): **{iva_usd:,.2f} USD**"
    .replace(",", "X").replace(".", ",").replace("X", ".")
)
st.write(
    f"Imposto provincial ({aliquota_prov:.1f}% sobre CIP Foz): **{imposto_prov_usd:,.2f} USD**"
    .replace(",", "X").replace(".", ",").replace("X", ".")
)
st.write(
    f"SIM (taxa fixa): **{valor_sim_usd:,.2f} USD**"
    .replace(",", "X").replace(".", ",").replace("X", ".")
)
st.write(
    f"INAL ({aliquota_inal:.1f}% sobre CIP Foz): **{inal_usd:,.2f} USD**"
    .replace(",", "X").replace(".", ",").replace("X", ".")
)

if mipymE_com_exclusao:
    st.info("Com exclusao MiPyME: nao ha percepcoes de IVA adicional nem Ganancias na importacao.")
else:
    st.write(
        f"IVA adicional ({aliquota_iva_adic:.1f}% sobre CIP Foz) – credito de IVA: "
        f"**{iva_adicional_usd:,.2f} USD**"
        .replace(",", "X").replace(".", ",").replace("X", ".")
    )
    st.write(
        f"Percepcao de Ganancias ({aliquota_ganancias:.1f}% sobre CIP Foz) – antecipacao IR: "
        f"**{ganancias_usd:,.2f} USD**"
        .replace(",", "X").replace(".", ",").replace("X", ".")
    )

st.write(
    f"Impostos nao recuperaveis (provincial + SIM + INAL): "
    f"**{impostos_nao_recuperaveis_usd:,.2f} USD**"
    .replace(",", "X").replace(".", ",").replace("X", ".")
)
st.write(
    f"Impostos recuperaveis (IVA + IVA adicional): "
    f"**{impostos_recuperaveis_usd:,.2f} USD**"
    .replace(",", "X").replace(".", ",").replace("X", ".")
)
if impostos_antecipados_ganancias_usd > 0:
    st.write(
        f"Percepcao Ganancias (antecipacao, nao entra no custo/kg): "
        f"**{impostos_antecipados_ganancias_usd:,.2f} USD**"
        .replace(",", "X").replace(".", ",").replace("X", ".")
    )

# ---------------------------------------------------------
# Conversao para BRL e ARS + cards
# ---------------------------------------------------------
st.markdown("### Conversao para reais e pesos")

custo_base_usd = total_corrientes_usd
total_sem_iva_usd = custo_base_usd + impostos_nao_recuperaveis_usd
total_com_iva_usd = total_sem_iva_usd + impostos_recuperaveis_usd
# Ganancias fica fora do custo, mas voce pode exibir separado depois se quiser

total_sem_iva_brl = total_sem_iva_usd * taxa_brl_usd
total_com_iva_brl = total_com_iva_usd * taxa_brl_usd

total_sem_iva_ars = total_sem_iva_usd * taxa_usd_ars
total_com_iva_ars = total_com_iva_usd * taxa_usd_ars

quantidade_kg = 2000.0

custo_sem_iva_por_kg_brl = total_sem_iva_brl / quantidade_kg if quantidade_kg > 0 else 0.0
custo_com_iva_por_kg_brl = total_com_iva_brl / quantidade_kg if quantidade_kg > 0 else 0.0

custo_sem_iva_por_kg_ars = total_sem_iva_ars / quantidade_kg if quantidade_kg > 0 else 0.0
custo_com_iva_por_kg_ars = total_com_iva_ars / quantidade_kg if quantidade_kg > 0 else 0.0

card_style = (
    "background-color:#041728;"
    "padding:18px 20px;"
    "border-radius:12px;"
    "border:1px solid #123456;"
)

col1, col2, col3 = st.columns(3)

# Card 1: custo sem IVA
total_sem_iva_brl_str = f"{total_sem_iva_brl:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
custo_sem_iva_por_kg_brl_str = f"{custo_sem_iva_por_kg_brl:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
custo_sem_iva_por_kg_ars_str = f"{custo_sem_iva_por_kg_ars:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

with col1:
    st.markdown(
        f"""
        <div style="{card_style}">
            <div style="color:#8FA3BF; font-size:13px; text-transform:uppercase;">
                CUSTO TOTAL SEM IVA
            </div>
            <div style="color:#FFFFFF; font-size:26px; font-weight:700; margin-top:4px;">
                R$ {total_sem_iva_brl_str}
            </div>
            <div style="color:#38D996; font-size:13px; margin-top:6px;">
                {custo_sem_iva_por_kg_brl_str} R$/kg · {custo_sem_iva_por_kg_ars_str} ARS/kg
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Card 2: custo com IVA
total_com_iva_brl_str = f"{total_com_iva_brl:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
custo_com_iva_por_kg_brl_str = f"{custo_com_iva_por_kg_brl:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
custo_com_iva_por_kg_ars_str = f"{custo_com_iva_por_kg_ars:,.0f}".replace(",", "X").replace(".", ",").replace("X", ".")

with col2:
    st.markdown(
        f"""
        <div style="{card_style}">
            <div style="color:#8FA3BF; font-size:13px; text-transform:uppercase;">
                CUSTO TOTAL COM IVA
            </div>
            <div style="color:#FFFFFF; font-size:26px; font-weight:700; margin-top:4px;">
                R$ {total_com_iva_brl_str}
            </div>
            <div style="color:#FF5C5C; font-size:13px; margin-top:6px;">
                {custo_com_iva_por_kg_brl_str} R$/kg · {custo_com_iva_por_kg_ars_str} ARS/kg
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Card 3: lote padrão
total_compra_str = total_str
with col3:
    st.markdown(
        f"""
        <div style="{card_style}">
            <div style="color:#8FA3BF; font-size:13px; text-transform:uppercase;">
                LOTE PADRAO
            </div>
            <div style="color:#FFFFFF; font-size:26px; font-weight:700; margin-top:4px;">
                2000 kg
            </div>
            <div style="color:#8FA3BF; font-size:12px; margin-top:6px;">
                Total compra: R$ {total_compra_str}<br>
                Produtos: R$ {prod_str}<br>
                Frete ate Foz: R$ {frete_str}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# Detalhamento em texto abaixo dos cards
st.write(
    f"Custo total SEM IVA (com provincial + SIM + INAL): "
    f"**{total_sem_iva_usd:,.2f} USD**, "
    f"**{total_sem_iva_brl:,.2f} BRL**, "
    f"**{total_sem_iva_ars:,.0f} ARS**"
    .replace(",", "X").replace(".", ",").replace("X", ".")
)
st.write(
    f"Custo total COM IVA (IVA + IVA adicional se houver + provincial + SIM + INAL): "
    f"**{total_com_iva_usd:,.2f} USD**, "
    f"**{total_com_iva_brl:,.2f} BRL**, "
    f"**{total_com_iva_ars:,.0f} ARS**"
    .replace(",", "X").replace(".", ",").replace("X", ".")
)
if impostos_antecipados_ganancias_usd > 0:
    st.write(
        f"Percepcao de Ganancias (nao incluida no custo/kg, mas impacta caixa): "
        f"**{impostos_antecipados_ganancias_usd:,.2f} USD**"
        .replace(",", "X").replace(".", ",").replace("X", ".")
    )
