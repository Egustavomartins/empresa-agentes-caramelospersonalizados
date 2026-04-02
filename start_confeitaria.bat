@echo off
cd /d H:\projetos\empresa-agentes
call venv\Scripts\activate.bat
start "" py -m streamlit run streamlit_app.py

