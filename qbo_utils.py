import os
import requests
from qbo_auth import refresh_qbo_access_token

QBO_ENVIRONMENT = os.getenv("QBO_ENVIRONMENT", "development")
MINOR_VERSION = "65"

API_BASE_URL = (
    "https://sandbox-quickbooks.api.intuit.com"
    if QBO_ENVIRONMENT == "development"
    else "https://quickbooks.api.intuit.com"
)


def _auth_headers():
    access_token = os.getenv("QBO_ACCESS_TOKEN")
    if not access_token:
        raise ValueError("QBO_ACCESS_TOKEN nao definido no .env")
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _get_with_refresh(url: str, params: dict):
    headers = _auth_headers()
    resp = requests.get(url, headers=headers, params=params)

    if resp.status_code in (401, 403):
        print(f"QBO: status {resp.status_code} recebido, tentando refresh de token...")
        refresh_qbo_access_token()
        headers = _auth_headers()
        resp = requests.get(url, headers=headers, params=params)

    resp.raise_for_status()
    return resp


# ============================================================
# 1) Relatorio de Lucros e Perdas
# ============================================================

def buscar_relatorio_lucros_perdas():
    realm_id = os.getenv("QBO_REALM_ID")
    if not realm_id:
        raise ValueError("QBO_REALM_ID nao definido no .env")

    url = f"{API_BASE_URL}/v3/company/{realm_id}/reports/ProfitAndLoss"
    params = {
        "minorversion": MINOR_VERSION,
        "date_macro": "This Month-to-date",
    }
    resp = _get_with_refresh(url, params)
    return resp.json()
    return resp.json()


def resumir_lucros_perdas(report_json):
    """
    Recebe o JSON do relatório de Lucros e Perdas e devolve
    um texto simples em português com receita, despesa, lucro
    e principais categorias.
    """
    header = report_json.get("Header", {})
    rows = report_json.get("Rows", {}).get("Row", [])

    start = header.get("StartPeriod")
    end = header.get("EndPeriod")

    total_income = "0.00"
    total_expenses = "0.00"
    net_income = "0.00"
    categorias_despesa = []

    for row in rows:
        group = row.get("group")
        # Total Income
        if group == "Income":
            summary = row.get("Summary", {})
            cols = summary.get("ColData", [])
            if len(cols) >= 2:
                total_income = cols[1].get("value", "0.00")
        # Total Expenses
        if group == "Expenses":
            summary = row.get("Summary", {})
            cols = summary.get("ColData", [])
            if len(cols) >= 2:
                total_expenses = cols[1].get("value", "0.00")

            # categorias dentro de Expenses
            inner_rows = row.get("Rows", {}).get("Row", [])
            for inner in inner_rows:
                if inner.get("type") == "Data":
                    cols_i = inner.get("ColData", [])
                    if len(cols_i) >= 2:
                        nome = cols_i[0].get("value")
                        valor = cols_i[1].get("value")
                        categorias_despesa.append(f"{nome}: {valor}")

        # Net Income
        if group == "NetIncome":
            summary = row.get("Summary", {})
            cols = summary.get("ColData", [])
            if len(cols) >= 2:
                net_income = cols[1].get("value", "0.00")

    categorias_str = (
        ", ".join(categorias_despesa[:5])
        if categorias_despesa
        else "Nenhuma categoria de despesa detalhada."
    )

    texto = (
        f"Periodo analisado: {start} a {end}.\n"
        f"Receita total: {total_income}.\n"
        f"Despesas totais: {total_expenses}.\n"
        f"Resultado (Lucro/Prejuizo): {net_income}.\n"
        f"Principais categorias de despesa: {categorias_str}.\n"
        "Os valores estao no padrao do QuickBooks (moeda e formato da empresa/sandbox).\n"
    )

    return texto


# ============================================================
# 2) Faturas (Invoices) - ultima fatura e resumo
# ============================================================

def buscar_ultima_fatura():
    realm_id = os.getenv("QBO_REALM_ID")
    if not realm_id:
        raise ValueError("QBO_REALM_ID nao definido no .env")

    url = f"{API_BASE_URL}/v3/company/{realm_id}/query"

    query_invoice = "SELECT * FROM Invoice ORDER BY MetaData.CreateTime DESC MAXRESULTS 5"
    params = {"minorversion": MINOR_VERSION, "query": query_invoice}

    resp = _get_with_refresh(url, params)
    data = resp.json()
    # DEBUG: descomente a linha abaixo se quiser inspecionar o retorno da API
    # print("DEBUG_INVOICES_QUERY:", data)
    invoices = data.get("QueryResponse", {}).get("Invoice", [])

    if invoices:
        return invoices[0]

    # 2) Se nao tiver Invoice, tenta SalesReceipt
    query_sr = "SELECT * FROM SalesReceipt ORDER BY MetaData.CreateTime DESC MAXRESULTS 5"
    params["query"] = query_sr

    resp2 = requests.get(url, headers=_auth_headers(), params=params)
    resp2.raise_for_status()
    data2 = resp2.json()
    # DEBUG: descomente se precisar ver SalesReceipt
    # print("DEBUG_SALESRECEIPT_QUERY:", data2)
    sales_receipts = data2.get("QueryResponse", {}).get("SalesReceipt", [])

    if sales_receipts:
        # Marca no json que e um SalesReceipt, so para sabermos no resumo se quisermos
        sr = sales_receipts[0]
        sr["_document_type"] = "SalesReceipt"
        return sr

    # Nao ha Invoice nem SalesReceipt
    return None

def resumir_fatura(invoice_json):
    """Gera um texto simples com os dados principais de uma fatura."""
    if not invoice_json:
        return "Nenhuma fatura encontrado no QuickBooks para resumir."

    numero = invoice_json.get("DocNumber", "sem numero")
    data = invoice_json.get("TxnDate", "")
    total = float(invoice_json.get("TotalAmt", 0))
    cliente = invoice_json.get("CustomerRef", {}).get("name", "Cliente nao informado")
    linhas = invoice_json.get("Line", [])

    # FATORES DO PACOTE (por 1 unidade vendida)
    # Caramelos Fruits Coracion y packing mate:
    # - 3,2 g de caramelos fruits coracion por unidade
    # - 0,5 g de film bopp kraft mate por unidade
    GRAMAS_CARAMELO_POR_UN = 3.2
    GRAMAS_BOPP_POR_UN = 0.5

    resumo_linhas = []
    consumo_caramelo_total_g = 0.0
    consumo_bopp_total_g = 0.0

    for line in linhas:
        if line.get("DetailType") != "SalesItemLineDetail":
            continue

        detalhes = line.get("SalesItemLineDetail", {})
        descricao = (
            line.get("Description")
            or detalhes.get("ItemRef", {}).get("name", "Item")
        )
        qty = float(detalhes.get("Qty", 0))
        rate = float(detalhes.get("UnitPrice", 0))

        linha_texto = f"- {descricao}: {qty} un x {rate:.2f}"

        # Se for o pacote de caramelos + packing, calcula consumo de MP
        if descricao.strip().lower() == "caramelos fruits coracion y packing mate".lower():
            consumo_caramelo = qty * GRAMAS_CARAMELO_POR_UN
            consumo_bopp = qty * GRAMAS_BOPP_POR_UN
            consumo_caramelo_total_g += consumo_caramelo
            consumo_bopp_total_g += consumo_bopp

            linha_texto += (
                f" (estimativa: consome {consumo_caramelo:.1f} g de Materia Prima Caramelos "
                f"Fruits Coracion e {consumo_bopp:.1f} g de Materia Prima Film Bopp Kraft Mate)"
            )

        resumo_linhas.append(linha_texto)

    texto_itens = "\n".join(resumo_linhas) if resumo_linhas else "Sem itens detalhados."

    extra_consumo = ""
    if consumo_caramelo_total_g > 0 or consumo_bopp_total_g > 0:
        consumo_caramelo_kg = consumo_caramelo_total_g / 1000.0
        consumo_bopp_kg = consumo_bopp_total_g / 1000.0
        extra_consumo = (
            f"\n\nResumo de consumo estimado de materia-prima nesta fatura:\n"
            f"- Materia Prima Caramelos Fruits Coracion: "
            f"{consumo_caramelo_total_g:.1f} g (~{consumo_caramelo_kg:.3f} kg)\n"
            f"- Materia Prima Film Bopp Kraft Mate: "
            f"{consumo_bopp_total_g:.1f} g (~{consumo_bopp_kg:.3f} kg)"
        )

    resumo = (
        f"Fatura {numero} em {data} para {cliente}.\n"
        f"Total da fatura: {total:.2f}.\n"
        f"Itens:\n{texto_itens}"
        f"{extra_consumo}"
    )
    return resumo


# ============================================================
# 3) Estoque (Inventory Items) - amostra simples
# ============================================================

def buscar_estoque_simplificado(max_results=20):
    realm_id = os.getenv("QBO_REALM_ID")
    if not realm_id:
        raise ValueError("QBO_REALM_ID nao definido no .env")

    url = f"{API_BASE_URL}/v3/company/{realm_id}/query"
    query = (
        "SELECT * FROM Item "
        "WHERE Type = 'Inventory' AND Active = true "
        f"MAXRESULTS {max_results}"
    )
    params = {"minorversion": MINOR_VERSION, "query": query}

    resp = _get_with_refresh(url, params)
    data = resp.json()
    items = data.get("QueryResponse", {}).get("Item", [])
    return items


def resumir_estoque(itens_json):
    """Gera um texto simples com os dados principais de estoque."""
    if not itens_json:
        return "Nenhum item de estoque encontrado no QuickBooks para resumir."

    linhas = []

    # Vamos guardar tambem custos para usar em outros calculos
    custo_car_kg = None
    custo_bopp_kg = None

    for item in itens_json:
        nome = item.get("Name", "Item sem nome")
        qty = float(item.get("QtyOnHand", 0))
        nome_lower = nome.strip().lower()

        avg_cost = item.get("AvgCost") or item.get("PurchaseCost") or 0.0
        avg_cost = float(avg_cost or 0.0)

        if nome_lower in [
            "materia prima caramelos  fruits coracion".lower(),
            "materia prima caramelos fruits coracion".lower(),
        ]:
            qty_kg = qty / 1000.0
            valor_int = int(qty_kg)  # truncado para simplificar
            linhas.append(
                f"- {nome}: {valor_int} kg de estoque atual."
            )
            if qty_kg > 0:
                # custo por kg ≈ valor total / kg (total = qty * avg_cost, mas avg_cost ja é por unidade; depende de como voce cadastrou)
                # aqui vamos assumir que avg_cost é custo por kg
                custo_car_kg = avg_cost

        elif nome_lower == "materia prima film bopp kraft mate".lower():
            qty_kg = qty / 1000.0
            valor_int = int(qty_kg)
            linhas.append(
                f"- {nome}: {valor_int} kg de estoque atual."
            )
            if qty_kg > 0:
                custo_bopp_kg = avg_cost

        else:
            linhas.append(f"- {nome}: {qty} unidades em estoque.")

    resumo_texto = (
        "Resumo de estoque (materia-prima em kg, demais itens em unidades):\n"
        + "\n".join(linhas)
    )

    # opcional: retornar tambem os custos para quem chamar
    return resumo_texto

