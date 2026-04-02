import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Chat Perplexity", layout="wide")

st.markdown(
    """
    <style>
    .stApp {
        background-color: #020814;
        color: #FFFFFF;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Chat Perplexity dentro do painel")
st.caption("Use o Perplexity sem sair deste navegador.")

components.iframe(
    "https://www.perplexity.ai",
    height=700,
    width=1200,
)
