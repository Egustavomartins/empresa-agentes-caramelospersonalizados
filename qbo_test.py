import os
import webbrowser
from urllib.parse import urlencode, urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer

import requests
from dotenv import load_dotenv

load_dotenv()

QBO_CLIENT_ID = os.getenv("QBO_CLIENT_ID")
QBO_CLIENT_SECRET = os.getenv("QBO_CLIENT_SECRET")
QBO_REDIRECT_URI = os.getenv("QBO_REDIRECT_URI")
QBO_ENVIRONMENT = os.getenv("QBO_ENVIRONMENT", "development")

# Endpoints da Intuit (para Development/Sandbox)
AUTH_BASE_URL = "https://appcenter.intuit.com/connect/oauth2"
TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"
API_BASE_URL = "https://sandbox-quickbooks.api.intuit.com"  # Development/sandbox


class OAuthHandler(BaseHTTPRequestHandler):
    # Servidor HTTP simples para capturar o "code" e o "realmId" de retorno da Intuit
    def do_GET(self):
        query = urlparse(self.path).query
        params = parse_qs(query)
        code = params.get("code", [None])[0]
        realm_id = params.get("realmId", [None])[0]

        if code:
            self.server.auth_code = code
            self.server.realm_id = realm_id
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Autorizacao concluida. Pode fechar esta janela.")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Erro: nao foi encontrado o parametro 'code'.")


def obter_auth_code_e_realm():
    # Monta a URL de autorizacao
    params = {
        "client_id": QBO_CLIENT_ID,
        "redirect_uri": QBO_REDIRECT_URI,
        "response_type": "code",
        "scope": "com.intuit.quickbooks.accounting",
        "state": "guga-teste-123",
    }
    auth_url = f"{AUTH_BASE_URL}?{urlencode(params)}"

    # Abre o navegador para voce logar e autorizar
    print("Abrindo navegador para autorizacao do QuickBooks...")
    webbrowser.open(auth_url)

    # Sobe um servidor local para receber o callback
    server_address = ("", 8000)
    httpd = HTTPServer(server_address, OAuthHandler)
    httpd.handle_request()  # espera apenas uma requisicao

    return getattr(httpd, "auth_code", None), getattr(httpd, "realm_id", None)


def trocar_code_por_token(auth_code):
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": QBO_REDIRECT_URI,
    }
    resp = requests.post(
        TOKEN_URL,
        headers=headers,
        data=urlencode(data),
        auth=(QBO_CLIENT_ID, QBO_CLIENT_SECRET),
    )
    resp.raise_for_status()
    return resp.json()


if __name__ == "__main__":
    # 1) Obter authorization code e realmId automaticamente
    code, realm_id = obter_auth_code_e_realm()
    if not code:
        print("Nao foi possivel obter o authorization code.")
        exit(1)

    print("Authorization code obtido:", code)
    print("Realm ID obtido:", realm_id)

    # 2) Trocar pelo access token
    token_data = trocar_code_por_token(code)
    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")

    print("\n===== COPIE O ACCESS TOKEN ABAIXO (SEM ESPACOS) =====\n")
    print(access_token)
    print("\n===== FIM DO ACCESS TOKEN =====\n")

    print("Refresh token (guarde em local seguro para renovar depois):")
    print((refresh_token or "")[:40], "...")
