import os
import streamlit as st

st.set_page_config(page_title="Comércio de brindes do Gustavo", layout="wide")

# Detecta se crewai está disponível (para não derrubar o app na nuvem)
try:
    import crewai  # noqa: F401
    CREWAI_OK = True
except Exception:
    CREWAI_OK = False

# Páginas
resumo_page = st.Page(
    "page_resumo_mes.py",
    title="Visao rapida do mes",
    icon="📊",
)

chat_page = st.Page(
    "page_chat.py",
    title="Chat com o time" if CREWAI_OK else "Chat (indisponível neste ambiente)",
    icon="💬",
)

custo_import_caramelo_page = st.Page(
    "page_custo_importacao_caramelo.py",
    title="Custo importacao caramelos (2000 kg)",
    icon="🍬",
)

custo_import_bopp_page = st.Page(
    "page_custo_importacao_bopp.py",
    title="Custo importacao Filme BOPP fosco (600 kg)",
    icon="🧻",
)

calculadora_page = st.Page(
    "page_calculadora.py",
    title="Calculadora cambial",
    icon="🧮",
)

simulacao_pacotes_page = st.Page(
    "page_simulacao_pacotes_balas.py",
    title="Simulação pacotes de balas",
    icon="🍭",
)

config_cambio_page = st.Page(
    "page_config_cambio.py",
    title="Configurar câmbio",
    icon="💱",
)

pg = st.navigation(
    [
        resumo_page,
        chat_page,
        custo_import_caramelo_page,
        custo_import_bopp_page,
        calculadora_page,
        simulacao_pacotes_page,
        config_cambio_page,
    ]
)

pg.run()
