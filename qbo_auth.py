import os
import base64
import requests
from pathlib import Path

try:
    import streamlit as st
    # Detecta se está em nuvem pelo env var padrão do Streamlit Cloud
    IN_STREAMLIT_CLOUD = bool(os.getenv("STREAMLIT_RUNTIME"))
except Exception:
    st = None
    IN_STREAMLIT_CLOUD = False

BASE_DIR = Path(__file__).resolve().parent

if IN_STREAMLIT_CLOUD:
    # Nuvem: usa st.secrets
    SECRETS = st.secrets
else:
    # Local / dev: usa .env
    from dotenv import load_dotenv

    load_dotenv(BASE_DIR / ".env")
    SECRETS = os.environ

TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"


def _get_secret(key: str) -> str | None:
    if isinstance(SECRETS, dict):
        return SECRETS.get(key)
    return os.getenv(key)


def _basic_auth_header() -> str:
    client_id = _get_secret("QBO_CLIENT_ID")
    client_secret = _get_secret("QBO_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError("QBO_CLIENT_ID ou QBO_CLIENT_SECRET nao definidos")

    raw = f"{client_id}:{client_secret}".encode("utf-8")
    return base64.b64encode(raw).decode("utf-8")


def refresh_qbo_access_token() -> str:
    """Usa o refresh_token atual para pegar um novo access_token."""
    refresh_token = _get_secret("QBO_REFRESH_TOKEN")
    if not refresh_token:
        raise ValueError("QBO_REFRESH_TOKEN nao definido nas secrets/.env")

    headers = {
        "Authorization": f"Basic {_basic_auth_header()}",
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    resp = requests.post(TOKEN_URL, headers=headers, data=data)
    try:
        resp.raise_for_status()
    except Exception:
        print("Erro ao renovar token QBO:", resp.status_code, resp.text)
        raise

    token_json = resp.json()
    new_access = token_json.get("access_token")
    new_refresh = token_json.get("refresh_token")

    if not new_access or not new_refresh:
        raise ValueError(f"Resposta invalida ao atualizar token: {token_json}")

    # Atualiza em memória
    os.environ["QBO_ACCESS_TOKEN"] = new_access
    os.environ["QBO_REFRESH_TOKEN"] = new_refresh
    print("QBO: token renovado (inicio):", new_access[:20])

    # Só tenta escrever .env quando estiver local
    if not IN_STREAMLIT_CLOUD:
        env_path = BASE_DIR / ".env"
        if env_path.exists():
            text = env_path.read_text(encoding="utf-8")
            import re

            if "QBO_ACCESS_TOKEN=" in text:
                text = re.sub(
                    r"^QBO_ACCESS_TOKEN=.*$",
                    f"QBO_ACCESS_TOKEN={new_access}",
                    text,
                    flags=re.MULTILINE,
                )
            else:
                text += f"\nQBO_ACCESS_TOKEN={new_access}"

            if "QBO_REFRESH_TOKEN=" in text:
                text = re.sub(
                    r"^QBO_REFRESH_TOKEN=.*$",
                    f"QBO_REFRESH_TOKEN={new_refresh}",
                    text,
                    flags=re.MULTILINE,
                )
            else:
                text += f"\nQBO_REFRESH_TOKEN={new_refresh}"

            env_path.write_text(text, encoding="utf-8")

    return new_access
