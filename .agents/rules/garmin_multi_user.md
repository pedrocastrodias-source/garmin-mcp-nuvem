# Guia de Configuração e Adição de Usuários - Garmin MCP Multi-Tenant

Este documento serve como a memória permanente para gerenciar o servidor Garmin MCP Multi-Usuário hospedado no Render.com. Ele detalha o que funcionou, o que deu errado (lições aprendidas) e o processo passo a passo para adicionar novos usuários.

---

## 🛠️ Lições Aprendidas (O que deu errado e como foi corrigido)

### 1. Bloqueio de Marca Registrada no Claude.ai (Trademark Filters)
*   **Problema:** Se o nome do conector (tanto no título do servidor FastMCP quanto no campo "Nome" digitado na interface do Claude) contiver a palavra `"Garmin"`, o Claude.ai bloqueia a conexão e exibe um erro exigindo chaves comerciais de OAuth (*"Não foi possível registrar no serviço de login de Garmin..."*).
*   **Solução:** 
    *   No código (`server_multi.py`), o título da aplicação é genérico: `app = FastMCP(f"Treinos {user_name}")`.
    *   No cadastro da interface do Claude, o usuário deve nomear o conector sem a palavra "Garmin" (ex: `Treinos Paulo`).

### 2. Bloqueio de IP da Garmin na Nuvem (Rate Limit 403 / 429)
*   **Problema:** O IP dos servidores do Render.com é compartilhado e frequentemente bloqueado pela Garmin por excesso de requisições. Se o conector tentar fazer login por e-mail e senha a cada reinicialização, ele falhará.
*   **Solução:** Login por Tokens Base64 (`GARMIN_TOKENS_BASE64`). Ao rodar um login local e exportar o token codificado, o servidor na nuvem entra diretamente reutilizando a sessão sem bater nas telas de e-mail/senha da Garmin, contornando o bloqueio de IP.

### 3. Starlette BaseHTTPMiddleware vs SSE Streams
*   **Problema:** O uso de `BaseHTTPMiddleware` para tirar o buffering do Render converte a transmissão contínua do Event-Stream (SSE) em uma resposta síncrona com buffer. Isso causava timeout no Claude Mobile.
*   **Solução:** Usar middleware ASGI de baixo nível (`PreventBufferingASGIMiddleware`) que intercepta apenas o evento `http.response.start` para injetar os cabeçalhos sem ler ou travar o corpo da mensagem.

### 4. Mudanças da Versão Standalone do `fastmcp` (v3.x)
*   **Erro:** `AttributeError: 'FastMCP' object has no attribute 'settings'`
    *   *Solução:* Configurar via objeto de módulo global `fastmcp.settings.http_host_origin_protection = False`.
*   **Erro:** `AttributeError: 'FastMCP' object has no attribute '_tool_manager'`
    *   *Solução:* Obter ferramentas registradas de `app.local_provider._components.items()` onde `key.startswith("tool:")`.
*   **Erro:** `AttributeError: 'FastMCP' object has no attribute 'sse_app'`
    *   *Solução:* Chamar `app.http_app(transport="sse")` para registrar corretamente as rotas `/sse` e `/messages`.

---

## 🚀 Passo a Passo para Adicionar um Novo Usuário

Ao adicionar uma nova pessoa (ex: "Maria"), siga estas etapas simples:

### 1. Gerar os Tokens Base64 Localmente
Na máquina local do Pedro, execute o script de login para autenticar a conta e salvar o arquivo de chaves codificado:
```python
import os, base64
from garminconnect import Garmin

email = "maria_email@gmail.com"
password = "maria_password_aqui"
token_dir = os.path.expanduser("~/.garminconnect_maria")
os.makedirs(token_dir, exist_ok=True)

g = Garmin(email=email, password=password)
g.login()
g.client.dump(token_dir)

with open(os.path.join(token_dir, "garmin_tokens.json"), "r", encoding="utf-8") as f:
    token_data = f.read()
b64 = base64.b64encode(token_data.encode()).decode()

with open(r"c:\Users\pedro\OneDrive\Garmin antigravity\MARIA_B64.txt", "w", encoding="utf-8") as fOut:
    fOut.write(b64)
```

### 2. Atualizar o `server_multi.py`
No arquivo `server_multi.py`, adicione a nova pessoa no método `get_master_app()`:

```python
# 1. Obter credenciais e tokens
maria_email = os.getenv("MARIA_EMAIL") or "maria_email@gmail.com"
maria_pass = os.getenv("MARIA_PASSWORD") or "maria_password_aqui"
maria_b64 = os.getenv("MARIA_TOKENS_BASE64")
maria_tokenstore = os.getenv("MARIA_TOKENSTORE") or "~/.garminconnect_maria"

# 2. Criar a aplicação individual
maria_sse = create_user_mcp_app("Maria", maria_email, maria_pass, maria_tokenstore, maria_b64)

# 3. Adicionar as rotas de Mount no Starlette
routes = [
    # ...
    Mount("/mariagarminsolucao123", app=maria_sse),
    Mount("/maria", app=maria_sse),
]
```

### 3. Fazer Commit e Push para o GitHub
```bash
git add garmin_mcp_server/src/garmin_mcp/server_multi.py MARIA_B64.txt
git commit -m "Add Maria to multi-user server configuration"
git push origin main
```

### 4. Configurar no Render.com Dashboard
*   Adicione a variável de ambiente `MARIA_TOKENS_BASE64` no painel do Render colando o conteúdo do arquivo `MARIA_B64.txt`.
*   Clique em **Save Changes**.

### 5. Cadastrar no Claude da Pessoa
*   **Nome:** `Treinos Maria`
*   **URL:** `https://garmin-mcp-nuvem.onrender.com/maria/sse`
