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

# --- LLM (mesmo do main.py) ---
llm = LLM(
    model=os.getenv("GROQ_MODEL"),
    base_url=os.getenv("GROQ_API_BASE_URL"),
    api_key=os.getenv("GROQ_API_KEY"),
)

# --- Agentes (reaproveitados do main.py) ---

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

# Agente coordenador para orquestrar os outros
coordenador = Agent(
    llm=llm,
    role="Coordenador financeiro e operacional",
    goal=(
        "Entender a pergunta do Gustavo, decidir como usar o contador e o gestor de estoque, "
        "e devolver uma resposta unica, clara e pratica."
    ),
    backstory=(
        "Voce coordena o time de agentes (contador e gestor de estoque) e sempre tenta dar ao dono da empresa "
        "uma visao clara para tomada de decisao."
    ),
    verbose=True,
)

crew = Crew(
    agents=[coordenador, contabil_agent, estoque_agent],
    tasks=[],
    llm=llm,
)


def criar_task_chat(pergunta_usuario: str) -> Task:
    """Cria uma task dinamica a partir da pergunta digitada no chat."""
    # Dados atuais do QBO
    report_json = buscar_relatorio_lucros_perdas()
    resumo_qbo = resumir_lucros_perdas(report_json)

    invoice = buscar_ultima_fatura()
    resumo_fat = resumir_fatura(invoice)

    itens_estoque = buscar_estoque_simplificado()
    resumo_est = resumir_estoque(itens_estoque)

          descricao = (
        "Voce e o coordenador do time (contador e gestor de estoque) da confeitaria do Gustavo.\n"
        "Abaixo estao alguns dados atualizados do QuickBooks (relatorio financeiro, ultima fatura e resumo de estoque):\n\n"
        f"[RESUMO FINANCEIRO]\n{resumo_qbo}\n\n"
        f"[ULTIMA FATURA]\n{resumo_fat}\n\n"
        f"[ESTOQUE]\n{resumo_est}\n\n"
        "AGORA, RESPONDA SOMENTE NO FORMATO ABAIXO, USANDO EXATAMENTE ESTES TITULOS E NESTA ORDEM:\n\n"
        "1) ANALISE DO CONTADOR\n"
        "2) ANALISE DO GESTOR DE ESTOQUE\n"
        "3) RESUMO PARA O GUSTAVO\n\n"
        "- Em 'ANALISE DO CONTADOR', fale apenas de receita, despesas (se existirem), resultado do mes em pesos e alertas financeiros.\n"
        "- Em 'ANALISE DO GESTOR DE ESTOQUE', fale apenas de estoque de materia-prima e capacidade de producao de brindes, "
        "deixando claro se ha risco de falta ou se ha apenas excesso de estoque.\n"
        "- Em 'RESUMO PARA O GUSTAVO', em ate 5 linhas, diga o que ele deveria fazer agora.\n\n"
        f"PERGUNTA DO GUSTAVO: {pergunta_usuario}\n\n"
        "REGRAS OBRIGATORIAS:\n"
        "- Nao use nenhum outro titulo alem de '1) ANALISE DO CONTADOR', '2) ANALISE DO GESTOR DE ESTOQUE' e '3) RESUMO PARA O GUSTAVO'.\n"
        "- Nao escreva introducao, conclusao ou qualquer texto fora desses tres blocos.\n"
        "- A moeda corrente e pesos argentinos (ARS); nunca use o simbolo R$ nem $. "
        "Sempre escreva os valores como 'X pesos' ou 'X pesos argentinos'.\n"
        "- Escreva em portugues simples e direto."
    )




    task = Task(
        description=descricao,
        expected_output="Uma resposta em portugues, organizada em secoes, respondendo a pergunta do Gustavo.",
        agent=coordenador,
        verbose=True,
    )

    return task


def loop_chat():
    print("=== Chat com agentes (Contador + Gestor de estoque) ===")
    print("Digite sua pergunta. Para sair, digite: sair\n")

    while True:
        pergunta = input("Você: ").strip()
        if not pergunta:
            continue
        if pergunta.lower() in ["sair", "exit", "quit"]:
            print("Encerrando chat.")
            break

        task = criar_task_chat(pergunta)
        crew.tasks = [task]

        resultado = crew.kickoff()
texto = str(resultado)

# 1) Força moeda em pesos (substitui "R$" por "pesos")
texto = texto.replace("R$ ", "").replace("R$", "")
# Se quiser sufixar:
# texto = texto.replace("R$ ", "").replace("R$", "") + " pesos"

# 2) Tenta reorganizar em 3 blocos se o modelo não obedeceu
if "ANALISE DO CONTADOR" not in texto:
    texto_formatado = (
        "1) ANALISE DO CONTADOR\n"
        "Aqui o modelo nao separou corretamente os blocos, mas o resumo financeiro e:\n"
    )
    # puxa só o trecho de situação do mês
    if "Situação do Mês" in texto:
        texto_formatado += texto.split("Situação do Mês", 1)[-1].split("##", 1)[0].strip()
    else:
        texto_formatado += texto.strip()

    texto_formatado += "\n\n2) ANALISE DO GESTOR DE ESTOQUE\n"
    if "Situação do Estoque" in texto:
        texto_formatado += texto.split("Situação do Estoque", 1)[-1].split("##", 1)[0].strip()
    else:
        texto_formatado += "\n(Estoque descrito acima.)"

    texto_formatado += "\n\n3) RESUMO PARA O GUSTAVO\n"
    texto_formatado += "O mes apresenta receita positiva em pesos e estoque de materia-prima abundante, sem risco de falta para brindes no curto prazo. O foco deve ser controlar despesas, girar o estoque e alinhar producao com a demanda.\n"

    texto = texto_formatado

print("\n--- Resposta dos agentes ---\n")
print(texto)
print("\n----------------------------\n")



if __name__ == "__main__":
    loop_chat()
