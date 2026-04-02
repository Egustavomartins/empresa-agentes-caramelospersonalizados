import os
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st
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

# --- Agentes (iguais aos do chat_agentes.py) ---

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
    verbose=False,
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
    verbose=False,
)

coordenador = Agent(
    llm=llm,
    role="Coordenador financeiro e operacional",
    goal=(
        "Entender a pergunta do Gustavo, decidir como usar o contador e o gestor de estoque, "
        "e devolver uma resposta unica, CLARA e BEM CURTA, focada em coisas praticas pra ele fazer."
    ),
    backstory=(
        "Voce coordena o time de agentes (contador e gestor de estoque) e sempre tenta dar ao dono da empresa "
        "uma visao clara, direta e acionavel, sem enrolacao, sem introducao longa e sem conclusao repetida."
    ),
    verbose=False,
)


crew = Crew(
    agents=[coordenador, contabil_agent, estoque_agent],
    tasks=[],
    llm=llm,
)


def perguntar_time(pergunta_usuario: str) -> str:
    """Monta contexto com QBO, pergunta para o coordenador e devolve texto já ajustado."""
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
        f"PERGUNTA DO GUSTAVO: {pergunta_usuario}\n\n"
        "Responda em portugues simples e direto, usando no maximo 8 frases curtas em formato de lista.\n"
        "Comece direto nos pontos importantes (sem introducao nem conclusao), foque em riscos e acoes praticas.\n"
        "Sempre use 'X pesos' ou 'X pesos argentinos' para valores de dinheiro (nunca use R$ nem $)."
    )

    task = Task(
        description=descricao,
        expected_output="Resposta em portugues, em secoes, para o dono da confeitaria.",
        agent=coordenador,
        verbose=False,
    )

    crew.tasks = [task]
    resposta = crew.kickoff()
    texto = str(resposta)

    # Ajuste simples de moeda
    texto = texto.replace("R$", "").replace("$", "")
    if "pesos" not in texto.lower():
        texto = texto + "\n\n(Valores em pesos argentinos.)"

    return texto


# --- App Streamlit ---

st.set_page_config(page_title="Chat - Confeitaria do Gustavo", layout="wide")
st.title("Chat com o time (contador + gestor de estoque)")

st.markdown(
    "Converse em tempo real com o time virtual que enxerga seus dados do QuickBooks "
    "e te responde em portugues."
)

# Inicializa histórico
if "messages" not in st.session_state:
    st.session_state.messages = []

# Mostra histórico
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input de chat
if prompt := st.chat_input("Digite sua pergunta para o time"):
    # Adiciona pergunta do usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Chama o time
    with st.chat_message("assistant"):
        with st.spinner("Consultando contador e gestor de estoque..."):
            resposta = perguntar_time(prompt)
            st.markdown(resposta)
    st.session_state.messages.append({"role": "assistant", "content": resposta})
