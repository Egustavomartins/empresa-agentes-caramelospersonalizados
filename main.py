import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, LLM

from qbo_utils import (
    buscar_relatorio_lucros_perdas,
    resumir_lucros_perdas,
    buscar_ultima_fatura,
    resumir_fatura,
    buscar_estoque_simplificado,
    resumir_estoque,
)

import smtplib
from email.mime.text import MIMEText

load_dotenv()

# Configura o LLM (Llama 3.x na Groq)
llm = LLM(
    model=os.getenv("GROQ_MODEL"),
    base_url=os.getenv("GROQ_API_BASE_URL"),
    api_key=os.getenv("GROQ_API_KEY"),
)

# Agente contábil
contabil_agent = Agent(
    llm=llm,
    role="Contador da empresa",
    goal=(
        "Analisar as movimentacoes financeiras do QuickBooks e explicar de forma simples "
        "para o dono da empresa o que esta bom, o que esta ruim e o que merece atencao."
    ),
    backstory=(
        "Voce e um contador experiente que trabalha com pequenas empresas no Brasil e na Argentina, "
        "acostumado com Simples Nacional, IVA e Monotributo. "
        "Voce explica tudo em linguagem simples, direta e pratica."
    ),
    verbose=True,
)

# Agente de estoque
estoque_agent = Agent(
    llm=llm,
    role="Gestor de estoque e producao",
    goal=(
        "Avaliar o estoque de materia-prima e produto acabado, identificar riscos de falta ou excesso "
        "e sugerir acoes praticas para melhorar o giro e o custo."
    ),
    backstory=(
        "Voce e um gestor de estoque que conhece bem producao de confeitaria, embalagens, BOPP e insumos. "
        "Voce sempre pensa em custo, validade e impacto no fluxo de caixa."
    ),
    verbose=True,
)


# FUNCAO PARA ENVIAR EMAIL DIRETO PELO SMTP DA TERRA
def enviar_email_relatorio(assunto: str, corpo: str):
    msg = MIMEText(corpo, "plain", "utf-8")
    msg["Subject"] = assunto
    msg["From"] = "gustavomartins@terra.com.br"
    msg["To"] = "gustavomartins@terra.com.br"

    with smtplib.SMTP_SSL("smtp.terra.com.br", 465) as server:
        server.login("gustavomartins@terra.com.br", "ratazanaretlide1506")
        server.send_message(msg)


# Task 1: analise financeira (lucros e perdas)
def criar_task_com_dados_qbo():
    # 1) Buscar relatorio bruto do QuickBooks (usa token do .env)
    report_json = buscar_relatorio_lucros_perdas()
    # 2) Resumir em texto simples
    resumo_qbo = resumir_lucros_perdas(report_json)

    descricao_tarefa = (
        "Voce e o contador da empresa de confeitaria do Gustavo.\n"
        "A moeda corrente da empresa e pesos argentinos (ARS).\n"
        "Nunca use o simbolo de real (R$) nem de peso ($). "
        "Sempre escreva os valores como 'X pesos' ou 'X pesos argentinos'.\n"
        "Abaixo estao os dados reais extraidos do QuickBooks Online "
        "para o periodo 'This Month-to-date':\n\n"
        f"{resumo_qbo}\n\n"
        "Com base nesses dados, produza um resumo unico para o dono com:\n"
        "1) Situacao geral do mes (financeiro) em pesos\n"
        "2) Principais alertas\n"
        "3) Sugestoes praticas para os proximos dias.\n"
        "Escreva tudo em portugues, de forma simples e direta, sempre citando valores em pesos argentinos."
    )

    task = Task(
        description=descricao_tarefa,
        expected_output=(
            "Um texto em portugues, organizado em secoes, com no maximo 30 linhas, "
            "contendo: visao geral do mes, alertas importantes e 3 a 5 acoes praticas recomendadas."
        ),
        agent=contabil_agent,
        verbose=True,
    )

    return task


# Task 2: analise de estoque + ultima fatura
def criar_task_estoque_qbo():
    # Buscar ultima fatura e resumo
    invoice = buscar_ultima_fatura()
    resumo_fat = resumir_fatura(invoice)

    # Buscar amostra de estoque e resumo
    itens_estoque = buscar_estoque_simplificado()
    resumo_est = resumir_estoque(itens_estoque)

    descricao = (
        "Voce e o gestor de estoque e producao da confeitaria do Gustavo.\n"
        "IMPORTANTE SOBRE UNIDADES E CAPACIDADE DE PRODUCAO:\n"
        "- Sempre trate 'Materia Prima Caramelos Fruits Coracion' e "
        "'Materia Prima Film Bopp Kraft Mate' como ESTOQUE EM KG, nunca em unidades.\n"
        "- Cada 1000 brindes de 'Caramelos Fruits Coracion y packing mate' consome 3,2 kg de "
        "Materia Prima Caramelos Fruits Coracion e 0,5 kg de Materia Prima Film Bopp Kraft Mate.\n"
        "- Compare SEMPRE o consumo estimado desta fatura com o volume total em estoque: "
        "se o estoque permitir produzir centenas de milhares de brindes e a fatura atual usar apenas alguns quilos, "
        "NAO fale em risco de falta dessa materia-prima nos proximos 15 dias; fale em excesso de estoque e capital parado.\n"
        "- So mencione risco de falta de materia-prima se o consumo projetado para os proximos 15 dias for relevante "
        "em relacao ao estoque total (por exemplo, se for consumir uma parte significativa do estoque, e nao uma fracao minima).\n"
        "A moeda corrente e pesos argentinos (ARS). Nao use simbolos como R$ ou $. Escreva sempre 'X pesos'.\n\n"
        "Abaixo estao os dados da ultima fatura emitida no QuickBooks Online "
        "e um resumo do estoque atual (amostra de itens de Inventory):\n\n"
        f"{resumo_fat}\n\n"
        f"{resumo_est}\n\n"
        "Com base nisso, responda:\n"
        "1) Riscos de falta OU excesso de estoque relacionados a essa fatura e aos proximos 15 dias, "
        "lembrando que, com estoques muito altos e consumo muito baixo, o risco principal e de excesso, nao de falta.\n"
        "2) Possiveis impactos no fluxo de caixa (compras necessarias, estoque parado).\n"
        "3) De 3 a 5 acoes praticas recomendadas (comprar, segurar compra, produzir, liquidar itens parados, etc.).\n"
        "Use o numero e o valor total da fatura no seu texto (por exemplo: 'na fatura 1006, de 221.430,00 pesos').\n"
        "Escreva em portugues, simples e direto, sempre falando de materia-prima em kg e focando mais em excesso de estoque "
        "do que em falta, quando for esse o caso."
    )

    task = Task(
        description=descricao,
        expected_output=(
            "Texto em portugues com 3 secoes: riscos de estoque, impacto no caixa e acoes praticas."
        ),
        agent=estoque_agent,
        verbose=True,
    )

    return task


crew = Crew(
    agents=[contabil_agent, estoque_agent],
    tasks=[],  # vamos adicionar as tasks em tempo de execucao
    llm=llm,
)

if __name__ == "__main__":
    analise_dia_task = criar_task_com_dados_qbo()
    estoque_task = criar_task_estoque_qbo()

    crew.tasks = [analise_dia_task, estoque_task]

    resultado = crew.kickoff()

    print("\n===== RELATORIO CONTABIL =====\n")
    print(analise_dia_task.output.raw)

    print("\n===== RELATORIO ESTOQUE / FATURA =====\n")
    print(estoque_task.output.raw)

    # monta um único texto para o e-mail
    corpo_email = (
        "RELATORIO CONTABIL\n\n"
        + analise_dia_task.output.raw
        + "\n\nRELATORIO ESTOQUE / FATURA\n\n"
        + estoque_task.output.raw
    )

    enviar_email_relatorio(
        assunto="Relatorio Caramelos Personalizados",
        corpo=corpo_email,
    )

    print("E-mail de relatorio enviado para gustavomartins@terra.com.br")

