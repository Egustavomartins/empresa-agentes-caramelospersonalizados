import os
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
from html import escape

from qbo_utils import (
    buscar_relatorio_lucros_perdas,
    resumir_lucros_perdas,
    buscar_estoque_simplificado,
    resumir_estoque,
    buscar_ultima_fatura,
    resumir_fatura,
)

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=str(BASE_DIR / ".env"))

# Le custos oficiais por kg do .env
CUSTO_CAR_KG_ENV = float(os.getenv("QBO_CUSTO_CARAMELOS_KG", "0") or 0)
CUSTO_BOPP_KG_ENV = float(os.getenv("QBO_CUSTO_BOPP_KG", "0") or 0)

# Tema escuro / textos brancos igual calculadora
st.set_page_config(page_title="Visao rapida do mes", layout="wide")

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

card_style = (
    "background-color:#041728;"
    "padding:18px 20px;"
    "border-radius:12px;"
    "border:1px solid #123456;"
)


def main():
    st.title("Visao rapida do mes")
    st.caption("Resumo rápido de ponto de equilíbrio, custos e visão geral do mês.")

    # =========================
    # Ponto de equilibrio
    # =========================
    st.markdown("### Ponto de equilibrio (estimativa)")

    # (Se precisar de itens depois, ja deixa carregado)
    try:
        itens = buscar_estoque_simplificado()
    except Exception as e:
        itens = []
        st.error(f"Erro ao buscar estoque para calcular custos: {e}")

    col_pe1, col_pe2, col_pe3 = st.columns(3)

    # Preco de venda por 1000 balas (em pesos)
    preco_1000 = col_pe1.number_input(
        "Preco de venda por 1000 balas (pesos)",
        min_value=0.0,
        value=120000.0,
        step=1000.0,
    )

    # Custos de MP por kg vindos do .env
    custo_car_kg = col_pe2.number_input(
        "Custo 1 kg caramelos (pesos, sem IVA)",
        min_value=0.0,
        value=CUSTO_CAR_KG_ENV,
        step=100.0,
    )

    custo_bopp_kg = col_pe3.number_input(
        "Custo 1 kg Bopp (pesos, sem IVA)",
        min_value=0.0,
        value=CUSTO_BOPP_KG_ENV,
        step=100.0,
    )

    st.markdown("---")
    st.markdown("### Custos fixos, folha e pro-labore (em pesos argentinos)")

    # taxa de cambio usada em todo o app
    TAXA_BRL_ARS = 267.0  # ajuste se quiser

    col_fix1, col_fix2, col_fix3 = st.columns(3)

    # Custo fixo "outros" (aluguel, contador, energia, etc.), em reais convertidos
    custo_fixo_brl = col_fix1.number_input(
        "Outros custos fixos (reais, ex.: aluguel, contador)",
        min_value=0.0,
        value=10000.0,
        step=500.0,
    )
    outros_fixos_pesos = custo_fixo_brl * TAXA_BRL_ARS

    # Dados de folha
    salario_bruto_medio = col_fix2.number_input(
        "Salario bruto medio por funcionario (pesos)",
        min_value=0.0,
        value=1000.0,
        step=50000.0,
    )

    qtd_funcionarios = col_fix3.number_input(
        "Quantidade de funcionarios",
        min_value=0,
        value=6,
        step=1,
    )

    col_fix4, col_fix5, col_fix6 = st.columns(3)

    perc_encargos = col_fix4.number_input(
        "Encargos patronais sobre salario bruto (%)",
        min_value=0.0,
        max_value=100.0,
        value=25.0,
        step=1.0,
        help="Percentual aproximado de encargos que a empresa paga sobre o salario bruto (cargas sociais).",
    )

    # Pró-labore dos sócios (em pesos)
    prolabore_por_socio_pesos = col_fix5.number_input(
        "Pro-labore bruto mensal por socio (pesos)",
        min_value=0.0,
        value=5000.0 * TAXA_BRL_ARS,
        step=50000.0,
    )

    qtd_socios = col_fix6.number_input(
        "Quantidade de socios com pro-labore",
        min_value=0,
        value=2,
        step=1,
    )

    col_fix7, col_fix8 = st.columns(2)

    perc_encargos_prolabore = col_fix7.number_input(
        "Encargos sobre pro-labore (%)",
        min_value=0.0,
        max_value=100.0,
        value=25.0,
        step=1.0,
        help="Percentual aproximado de encargos e impostos sobre o pro-labore (INSS/autonomos etc.).",
    )

    # Calcula custo de folha mensal em pesos
    custo_folha_pesos = 0.0
    if salario_bruto_medio > 0 and qtd_funcionarios > 0:
        custo_folha_pesos = salario_bruto_medio * qtd_funcionarios * (1 + perc_encargos / 100.0)

    # Calcula custo de pro-labore mensal em pesos
    custo_prolabore_pesos = 0.0
    if prolabore_por_socio_pesos > 0 and qtd_socios > 0:
        custo_prolabore_pesos = prolabore_por_socio_pesos * qtd_socios * (1 + perc_encargos_prolabore / 100.0)

    with col_fix8:
        st.markdown(
            f"Custo mensal estimado de folha (salario + encargos): "
            f"**{custo_folha_pesos:,.0f} pesos**.\n\n"
            f"Custo mensal estimado de pro-labore (todos os socios): "
            f"**{custo_prolabore_pesos:,.0f} pesos**."
            .replace(",", "X").replace(".", ",").replace("X", ".")
        )

    # Custo fixo total em pesos (outros + folha + pro-labore)
    custo_fixo_total_pesos = outros_fixos_pesos + custo_folha_pesos + custo_prolabore_pesos

    st.markdown(
        f"Custo fixo TOTAL estimado (outros + folha + pro-labore): "
        f"**{custo_fixo_total_pesos:,.0f} pesos**."
        .replace(",", "X").replace(".", ",").replace("X", ".")
    )

    # -----------------------------
    # Card resumo de custos (estilo calculadora)
    # -----------------------------
    st.markdown("### Resumo rápido dos custos fixos")

    col_c1, col_c2, col_c3 = st.columns(3)

    custo_fixo_total_brl = custo_fixo_total_pesos / TAXA_BRL_ARS if TAXA_BRL_ARS > 0 else 0.0

    with col_c1:
        st.markdown(
            f"""
            <div style="{card_style}">
                <div style="color:#8FA3BF; font-size:11px; text-transform:uppercase;">
                    OUTROS CUSTOS FIXOS
                </div>
                <div style="color:#FFFFFF; font-size:18px; font-weight:700; margin-top:4px;">
                    {outros_fixos_pesos:,.0f} pesos
                </div>
            </div>
            """.replace(",", "X").replace(".", ",").replace("X", "."),
            unsafe_allow_html=True,
        )

    with col_c2:
        st.markdown(
            f"""
            <div style="{card_style}">
                <div style="color:#8FA3BF; font-size:11px; text-transform:uppercase;">
                    FOLHA + PRO-LABORE
                </div>
                <div style="color:#FFFFFF; font-size:18px; font-weight:700; margin-top:4px;">
                    {(custo_folha_pesos + custo_prolabore_pesos):,.0f} pesos
                </div>
            </div>
            """.replace(",", "X").replace(".", ",").replace("X", "."),
            unsafe_allow_html=True,
        )

    with col_c3:
        st.markdown(
            f"""
            <div style="{card_style}">
                <div style="color:#8FA3BF; font-size:11px; text-transform:uppercase;">
                    CUSTO FIXO TOTAL
                </div>
                <div style="color:#FFFFFF; font-size:18px; font-weight:700; margin-top:4px;">
                    {custo_fixo_total_pesos:,.0f} pesos
                </div>
                <div style="color:#8FA3BF; font-size:13px; margin-top:6px;">
                    ≈ R$ {custo_fixo_total_brl:,.0f}
                </div>
            </div>
            """.replace(",", "X").replace(".", ",").replace("X", "."),
            unsafe_allow_html=True,
        )

    # Consumo de MP por 1000 balas
    GRAMAS_CARAMELO_POR_UN = 3.2  # g por bala
    GRAMAS_BOPP_POR_UN = 0.5      # g por bala

    kg_car_por_1000 = (GRAMAS_CARAMELO_POR_UN * 1000) / 1000.0  # 3,2 kg
    kg_bopp_por_1000 = (GRAMAS_BOPP_POR_UN * 1000) / 1000.0     # 0,5 kg

    custo_mp_1000 = kg_car_por_1000 * custo_car_kg + kg_bopp_por_1000 * custo_bopp_kg

    lucro_bruto_1000 = preco_1000 - custo_mp_1000

    pergunta_pronta_pe = ""
    pergunta_pronta_planejado = ""

    if lucro_bruto_1000 <= 0:
        st.error(
            "Com esse preco e esses custos, nao ha lucro bruto por 1000 balas "
            "(ou e negativo). Ajuste os valores."
        )
    else:
        n_pacotes = custo_fixo_total_pesos / lucro_bruto_1000 if custo_fixo_total_pesos > 0 else 0.0
        n_balas = 1000 * n_pacotes

        st.markdown(
            f"Lucro bruto por 1000 balas (estimado): **{lucro_bruto_1000:,.0f} pesos**."
            .replace(",", "X").replace(".", ",").replace("X", ".")
        )

        if custo_fixo_total_pesos > 0:
            st.markdown(
                f"Para pagar o custo fixo TOTAL (~{custo_fixo_total_pesos:,.0f} pesos), "
                f"voce precisa vender aproximadamente **{n_pacotes:,.1f} pacotes de 1000 balas** "
                f"(~**{n_balas:,.0f} balas**)."
                .replace(",", "X").replace(".", ",").replace("X", ".")
            )
            st.markdown(
                f"Com esses valores, seu ponto de equilibrio e vender cerca de "
                f"**{n_balas:,.0f} balas por mes**. A partir desse volume, o lucro bruto "
                f"passa a cobrir todos os custos fixos (incluindo folha e pro-labore) e comeca a virar lucro liquido."
                .replace(",", "X").replace(".", ",").replace("X", ".")
            )
        else:
            st.info(
                "Defina os custos fixos (outros + folha + pro-labore) para ver o ponto de equilibrio."
            )

        # Pergunta pronta relacionada ao ponto de equilibrio
        if custo_fixo_total_pesos > 0:
            pergunta_pronta_pe = (
                "Explique em portugues simples o que significa este ponto de equilibrio e se o preco atual faz sentido "
                f"para o meu negocio. Considere que:\n"
                f"- Preco de venda por 1000 balas: {preco_1000:.2f} pesos.\n"
                f"- Lucro bruto por 1000 balas: {lucro_bruto_1000:.2f} pesos.\n"
                f"- Custo fixo mensal TOTAL (outros + folha + pro-labore): {custo_fixo_total_pesos:.0f} pesos.\n"
                f"- Preciso vender aproximadamente {n_pacotes:,.1f} pacotes de 1000 balas (~{n_balas:,.0f} balas) para pagar o fixo.\n"
                "Fale se esse nivel de vendas parece realista e se o preco esta adequado, pensando em risco de estoque, folha, pro-labore e fluxo de caixa."
            ).replace(",", "X").replace(".", ",").replace("X", ".")

            st.markdown("---")
            st.markdown("**Pergunta pronta (ponto de equilibrio) para o chat:**")
            st.code(pergunta_pronta_pe)

        # =========================
        # Parametros de impostos
        # =========================
        st.markdown("### Impostos sobre o resultado (simulacao)")

        col_imp1, col_imp2 = st.columns(2)

        aliquota_iibb = col_imp1.number_input(
            "Aliquota de Ingresos Brutos (% sobre faturamento)",
            min_value=0.0,
            max_value=10.0,
            value=3.5,
            step=0.1,
            help="Percentual aproximado de Impuesto sobre los Ingresos Brutos (IIBB) sobre o faturamento bruto.",
        )

        aliquota_ganancias = col_imp2.number_input(
            "Aliquota de Ganancias (% sobre lucro antes do imposto)",
            min_value=0.0,
            max_value=40.0,
            value=25.0,
            step=1.0,
            help="Percentual aproximado de Impuesto a las Ganancias sobre o lucro contabel.",
        )

        # =========================
        # Planejamento de vendas (lucro liquido estimado)
        # =========================
        st.markdown("### Simulacao de lucro liquido com volume planejado")

        col_plan1, col_plan2 = st.columns(2)

        with col_plan1:
            balas_planejadas = st.number_input(
                "Balas planejadas para vender no mes",
                min_value=0.0,
                value=50000.0,
                step=1000.0,
            )

        lucro_liquido_planejado = None

        if balas_planejadas > 0 and custo_fixo_total_pesos > 0:
            pacotes_planejados = balas_planejadas / 1000.0
            receita_bruta = pacotes_planejados * preco_1000
            lucro_bruto_total = pacotes_planejados * lucro_bruto_1000

            # IIBB sobre faturamento
            valor_iibb = receita_bruta * (aliquota_iibb / 100.0)

            # lucro antes de Ganancias (apos custos fixos e IIBB)
            lucro_antes_ganancias = lucro_bruto_total - custo_fixo_total_pesos - valor_iibb

            # se lucro_antes_ganancias for negativo, Ganancias = 0
            valor_ganancias = 0.0
            if lucro_antes_ganancias > 0 and aliquota_ganancias > 0:
                valor_ganancias = lucro_antes_ganancias * (aliquota_ganancias / 100.0)

            lucro_liquido_planejado = lucro_antes_ganancias - valor_ganancias
            lucro_liquido_brl = lucro_liquido_planejado / TAXA_BRL_ARS if TAXA_BRL_ARS > 0 else 0.0

            with col_plan2:
                st.markdown(
                    f"Receita bruta com {balas_planejadas:,.0f} balas: "
                    f"**{receita_bruta:,.0f} pesos**.\n\n"
                    f"IIBB estimado ({aliquota_iibb:.1f}% sobre faturamento): "
                    f"**{valor_iibb:,.0f} pesos**.\n\n"
                    f"Lucro antes de Ganancias (apos custos fixos e IIBB): "
                    f"**{lucro_antes_ganancias:,.0f} pesos**.\n\n"
                    f"Ganancias estimado ({aliquota_ganancias:.1f}% sobre lucro): "
                    f"**{valor_ganancias:,.0f} pesos**.\n\n"
                    f"Lucro liquido estimado do mes (apos todos os custos fixos e impostos): "
                    f"**{lucro_liquido_planejado:,.0f} pesos** "
                    f"(aprox. **{lucro_liquido_brl:,.0f} reais**)."
                    .replace(",", "X").replace(".", ",").replace("X", ".")
                )

            # Pergunta pronta para o chat
            pergunta_pronta_planejado = (
                "Considere os seguintes numeros ja calculados pelo sistema (nao recalcular, apenas usar):\n"
                f"- Preco de venda por 1000 balas: {preco_1000:.2f} pesos.\n"
                f"- Lucro bruto por 1000 balas: {lucro_bruto_1000:.2f} pesos.\n"
                f"- Custo fixo mensal TOTAL (outros + folha + pro-labore): {custo_fixo_total_pesos:.0f} pesos.\n"
                f"- Volume planejado de vendas no mes: {balas_planejadas:,.0f} balas "
                f"({pacotes_planejados:,.1f} pacotes).\n"
                f"- Receita bruta estimada do mes: {receita_bruta:,.0f} pesos.\n"
                f"- IIBB estimado ({aliquota_iibb:.1f}% sobre faturamento): {valor_iibb:,.0f} pesos.\n"
                f"- Lucro antes de Ganancias (apos custos fixos e IIBB): {lucro_antes_ganancias:,.0f} pesos.\n"
                f"- Ganancias estimado ({aliquota_ganancias:.1f}% sobre lucro): {valor_ganancias:,.0f} pesos.\n"
                f"- Lucro liquido estimado do mes com esse volume: {lucro_liquido_planejado:,.0f} pesos.\n"
                "Explique em portugues simples se esse lucro liquido parece bom em relacao ao risco de estoque, "
                "ao esforco de vender esse volume, aos custos de folha, pro-labore e ao fluxo de caixa da confeitaria."
            ).replace(",", "X").replace(".", ",").replace("X", ".")

            st.markdown("---")
            st.markdown("**Pergunta pronta (lucro com volume planejado e impostos) para o chat:**")
            st.code(pergunta_pronta_planejado)

    st.markdown("---")

    # =========================
    # Resumos de QBO
    # =========================
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Lucros e perdas (resumo)")
        try:
            report = buscar_relatorio_lucros_perdas()
            resumo = resumir_lucros_perdas(report)
            st.markdown(
                "<div style='color:#FFFFFF; white-space:pre-wrap; font-family:Menlo, monospace; font-size:13px;'>"
                + escape(resumo) +
                "</div>",
                unsafe_allow_html=True,
            )
        except Exception as e:
            st.error(f"Erro ao buscar relatorio: {e}")

    with col2:
        st.subheader("Ultima fatura")
        try:
            inv = buscar_ultima_fatura()
            resumo_fat = resumir_fatura(inv)
            st.markdown(
                "<div style='color:#FFFFFF; white-space:pre-wrap; font-family:Menlo, monospace; font-size:13px;'>"
                + escape(resumo_fat) +
                "</div>",
                unsafe_allow_html=True,
            )
        except Exception as e:
            st.error(f"Erro ao buscar fatura: {e}")

    st.subheader("Estoque chave")
    try:
        if not itens:
            itens_local = buscar_estoque_simplificado()
        else:
            itens_local = itens
        resumo_est = resumir_estoque(itens_local)
        st.markdown(
            "<div style='color:#FFFFFF; white-space:pre-wrap; font-family:Menlo, monospace; font-size:13px;'>"
            + escape(resumo_est) +
            "</div>",
            unsafe_allow_html=True,
        )
    except Exception as e:
        st.error(f"Erro ao buscar estoque: {e}")


if __name__ == "__main__":
    main()

