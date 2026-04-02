import os
import base64
import requests
from pathlib import Path
try:
    import streamlit as st
    SECRETS = st.secrets
except Exception:
    from dotenv import load_dotenv

    BASE_DIR = Path(__file__).resolve().parent
    load_dotenv(BASE_DIR / ".env")
    SECRETS = os.environ

QBO_CLIENT_ID = SECRETS.get("QBO_CLIENT_ID")
QBO_CLIENT_SECRET = SECRETS.get("QBO_CLIENT_SECRET")
QBO_REDIRECT_URI = SECRETS.get("QBO_REDIRECT_URI")
QBO_ENVIRONMENT = SECRETS.get("QBO_ENVIRONMENT", "production")
QBO_REALM_ID = SECRETS.get("QBO_REALM_ID")

QBO_ACCESS_TOKEN = SECRETS.get("QBO_ACCESS_TOKEN")
QBO_REFRESH_TOKEN = SECRETS.get("QBO_REFRESH_TOKEN")

TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"


def _basic_auth_header() -> str:
    client_id = os.getenv("QBO_CLIENT_ID")
    client_secret = os.getenv("QBO_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError("QBO_CLIENT_ID ou QBO_CLIENT_SECRET nao definidos no .env")

    raw = f"{client_id}:{client_secret}".encode("utf-8")
    return base64.b64encode(raw).decode("utf-8")


def refresh_qbo_access_token() -> str:
    """Usa o refresh_token atual para pegar um novo access_token e atualiza o .env."""
    refresh_token = os.getenv("QBO_REFRESH_TOKEN")
    if not refresh_token:
        raise ValueError("QBO_REFRESH_TOKEN nao definido no .env")

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
    resp.raise_for_status()
    token_json = resp.json()

    new_access = token_json.get("access_token")
    new_refresh = token_json.get("refresh_token")

    if not new_access or not new_refresh:
        raise ValueError(f"Resposta invalida ao atualizar token: {token_json}")

    # Atualiza variaveis de ambiente em tempo de execucao
    os.environ["QBO_ACCESS_TOKEN"] = new_access
    os.environ["QBO_REFRESH_TOKEN"] = new_refresh
    print("QBO: token renovado (inicio):", new_access[:20])

    # Opcional: salvar de volta no .env (para persistir entre execucoes)
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        text = env_path.read_text(encoding="utf-8")
        if "QBO_ACCESS_TOKEN=" in text:
            # troca linha do access
            import re
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
