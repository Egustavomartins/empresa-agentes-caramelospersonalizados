import os
import re
from math import isclose
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

# Carrega .env a partir da pasta do projeto
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(dotenv_path=str(BASE_DIR / ".env"))


# --- LLM ---
llm = LLM(
    model=os.getenv("GROQ_MODEL"),
    base_url=os.getenv("GROQ_API_BASE_URL"),
    api_key=os.getenv("GROQ_API_KEY"),
)

# =========================
# Função de validação numérica
# =========================

def extrair_numeros(texto: str):
    """
    Extrai numeros (inteiros/decimais, com virgula ou ponto) da string como floats,
    tratando formatos tipo 120000,00 / 2.655.428 / 50.000.
    """
    # pega tokens com digitos, pontos e virgulas
    matches = re.findall(r"\d[\d\.,]*", texto)
    numeros = []

    for m in matches:
        t = m.strip()

        n_pontos = t.count(".")
        n_virg = t.count(",")

        if n_virg == 0 and n_pontos == 0:
            # apenas digitos
            try:
                numeros.append(float(t))
            except ValueError:
                continue
        elif n_virg == 1 and n_pontos >= 0:
            # formato PT-BR classico: 2.655.428,56 -> milhar com ponto, decimal com virgula
            t_clean = t.replace(".", "").replace(",", ".")
            try:
                numeros.append(float(t_clean))
            except ValueError:
                continue
        elif n_virg == 0 and n_pontos >= 1:
            # pode ser 2.655.428 (milhar) ou 120000.50 (decimal)
            if n_pontos > 1:
                # assume pontos como milhar
                t_clean = t.replace(".", "")
            else:
                # um único ponto: pode ser decimal; deixa como esta
                t_clean = t
            try:
                numeros.append(float(t_clean))
            except ValueError:
                continue
        else:
            # casos mais estranhos: normaliza tirando pontos e usando virgula como decimal
            t_clean = t.replace(".", "").replace(",", ".")
            try:
                numeros.append(float(t_clean))
            except ValueError:
                continue

    return numeros


def validar_resposta_numeros(resposta: str, numeros_permitidos: list[float], tolerancia_rel=0.02) -> bool:
    """
    Verifica se a resposta so usa numeros que estao dentro da lista de numeros_permitidos
    (com pequena tolerancia). Ignora numeros pequenos (< 5).
    """
    nums = extrair_numeros(resposta)
    if not nums:
        return True  # nao falou numero, entao ok

    for n in nums:
        if n < 5:
            # ignora numeros pequenos (ex.: 1, 2, 3 meses, etc.)
            continue

        ok = any(
            isclose(n, p, rel_tol=tolerancia_rel, abs_tol=tolerancia_rel * max(1.0, p))
            for p in numeros_permitidos
        )
        if not ok:
            return False
    return True


# --- Agentes ---

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
        "uma visao clara, direta e acionavel, sem enrolacao, sem introducao longa e sem conclusao repetida. "
        "IMPORTANTE: voce NAO PODE fazer contas. Quando receber numeros (precos, custos, lucros, ponto de equilibrio, estoque etc.), "
        "assuma que esses numeros ja estao corretos. Nunca recalcule ou invente novos numeros. "
        "Se precisar de um numero que nao foi informado, diga claramente que nao sabe esse numero."
    ),
    verbose=False,
)

crew = Crew(
    agents=[coordenador, contabil_agent, estoque_agent],
    tasks=[],
    llm=llm,
)


def montar_numeros_permitidos(pergunta_usuario: str) -> list[float]:
    """
    Extrai da pergunta do usuario os numeros que serao considerados 'verdade oficial'.
    Isso garante que o modelo so possa repetir o que veio da pagina (ex.: ponto de equilibrio).
    """
    return extrair_numeros(pergunta_usuario)


def perguntar_time(pergunta_usuario: str) -> str:
    """Monta contexto com QBO, pergunta para o coordenador e devolve texto ja ajustado."""
    report_json = buscar_relatorio_lucros_perdas()
    resumo_qbo = resumir_lucros_perdas(report_json)

    invoice = buscar_ultima_fatura()
    resumo_fat = resumir_fatura(invoice)

    itens_estoque = buscar_estoque_simplificado()
    resumo_est = resumir_estoque(itens_estoque)

    # numeros permitidos = o que veio da pergunta do usuario (ponto de equilibrio, preco, lucro etc.)
    numeros_permitidos = montar_numeros_permitidos(pergunta_usuario)

    descricao = (
        "Voce e o coordenador do time (contador e gestor de estoque) da confeitaria do Gustavo.\n"
        "Abaixo estao alguns dados atualizados do QuickBooks (relatorio financeiro, ultima fatura e resumo de estoque):\n\n"
        f"[RESUMO FINANCEIRO]\n{resumo_qbo}\n\n"
        f"[ULTIMA FATURA]\n{resumo_fat}\n\n"
        f"[ESTOQUE]\n{resumo_est}\n\n"
        "REGRAS MUITO IMPORTANTES (QUE VOCE NUNCA PODE QUEBRAR):\n"
        "1) Voce NAO PODE fazer nenhuma conta nem recalcular numeros.\n"
        "2) Todos os numeros informados pelo Gustavo (precos, custos, lucros, ponto de equilibrio, estoque etc.) "
        "ja foram calculados por outro sistema e estao corretos.\n"
        "3) Voce NUNCA deve inventar numero novo (valores de dinheiro, quantidades, percentuais etc.).\n"
        "4) Se precisar de um numero que nao estiver escrito na mensagem do Gustavo, responda claramente: "
        "'Nao sei esse numero, preciso que voce me informe.'\n"
        "5) Se o Gustavo pedir para voce calcular qualquer coisa, responda: "
        "'Nao posso fazer contas, apenas explicar os numeros que voce me passar.'\n\n"
        f"PERGUNTA DO GUSTAVO: {pergunta_usuario}\n\n"
        "Sua tarefa e SOMENTE explicar em portugues simples o que esses numeros representam, "
        "apontar riscos (estoque, fluxo de caixa, preco baixo ou alto) e sugerir proximos passos praticos.\n"
        "Responda em portugues simples e direto, usando no maximo 8 frases curtas em formato de lista.\n"
        "Comece direto nos pontos importantes (sem introducao nem conclusao), foque em riscos e acoes praticas.\n"
        "Sempre use 'X pesos' ou 'X pesos argentinos' para valores de dinheiro (nunca use R$ nem $).\n"
        "Nunca crie numeros novos ou diferentes dos que foram informados na pergunta."
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

    # =========================
    # Validação de números
    # =========================
    if numeros_permitidos:
        if not validar_resposta_numeros(texto, numeros_permitidos):
            texto = (
                "O assistente tentou usar numeros diferentes dos calculados pelo sistema. "
                "Por seguranca, considere apenas os numeros que voce ve na tela do ponto de equilibrio "
                "e tente refazer a pergunta, copiando os valores exatos."
            )

    return texto


def main():
    st.title("Chat com o time (contador + gestor de estoque)")

    st.markdown(
        "Converse em tempo real com o time virtual que enxerga seus dados do QuickBooks "
        "e te responde em portugues."
    )

    # Inicializa historico
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Mostra historico
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input de chat
    if prompt := st.chat_input("Digite sua pergunta para o time"):
        # Adiciona pergunta do usuario
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Chama o time
        with st.chat_message("assistant"):
            with st.spinner("Consultando contador e gestor de estoque..."):
                resposta = perguntar_time(prompt)
                st.markdown(resposta)
        st.session_state.messages.append({"role": "assistant", "content": resposta})


if __name__ == "__main__":
    main()
