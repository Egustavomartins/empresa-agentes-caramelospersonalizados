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


# Task 1: analise financeira (lucros e perdas)
def criar_task_com_dados_qbo():
    # 1) Buscar relatorio bruto do QuickBooks (usa token do .env)
    report_json = buscar_relatorio_lucros_perdas()
    # 2) Resumir em texto simples
    resumo_qbo = resumir_lucros_perdas(report_json)

    descricao_tarefa = (
        "Voce e o contador da empresa de confeitaria do Gustavo.\n"
        "Abaixo estao os dados reais extraidos do QuickBooks Online "
        "para o periodo 'This Month-to-date':\n\n"
        f"{resumo_qbo}\n\n"
        "Com base nesses dados, produza um resumo unico para o dono com:\n"
        "1) Situacao geral do mes (financeiro)\n"
        "2) Principais alertas\n"
        "3) Sugestoes praticas para os proximos dias.\n"
        "Escreva tudo em portugues, de forma simples e direta."
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
        "Abaixo estao os dados da ultima fatura emitida no QuickBooks Online "
        "e um resumo do estoque atual (amostra de itens de Inventory):\n\n"
        f"{resumo_fat}\n\n"
        f"{resumo_est}\n\n"
        "Com base nisso, responda:\n"
        "1) Riscos de falta ou excesso de estoque relacionados a essa fatura e aos proximos 15 dias\n"
        "2) Possiveis impactos no fluxo de caixa (compras necessarias, estoque parado)\n"
        "3) De 3 a 5 acoes praticas recomendadas (comprar, segurar compra, produzir, liquidar itens parados, etc.).\n"
        "Use o numero e o valor total da fatura no seu texto (por exemplo: 'na fatura 1006, de 221.430,00').\n"
        "Escreva em portugues, simples e direto."
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



