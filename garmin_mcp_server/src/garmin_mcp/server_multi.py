import os
import sys
import base64
import uvicorn
import contextvars
import functools
import inspect
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.responses import PlainTextResponse

from garminconnect import Garmin, GarminConnectAuthenticationError, GarminConnectConnectionError, GarminConnectTooManyRequestsError
from mcp.server.fastmcp import FastMCP

from garmin_mcp import (
    activity_management,
    health_wellness,
    user_profile,
    devices,
    gear_management,
    weight_management,
    challenges,
    training,
    workouts,
    workout_templates,
    data_management,
    womens_health,
    nutrition,
    workout_builders,
    courses,
    activity_analysis,
)

# ContextVar to hold the active client in the async/coroutine context
current_garmin_client = contextvars.ContextVar("current_garmin_client", default=None)

class GarminClientProxy:
    """Proxy object that routes attribute/method access to the active context's client."""
    def __getattr__(self, name):
        client = current_garmin_client.get()
        if client is None:
            raise RuntimeError("No active Garmin client in this context")
        return getattr(client, name)

    def __bool__(self):
        return current_garmin_client.get() is not None

# Single global proxy instance used to configure all modules once
client_proxy = GarminClientProxy()

# Configure all modules to point to the proxy
activity_management.configure(client_proxy)
health_wellness.configure(client_proxy)
user_profile.configure(client_proxy)
devices.configure(client_proxy)
gear_management.configure(client_proxy)
weight_management.configure(client_proxy)
challenges.configure(client_proxy)
training.configure(client_proxy)
workouts.configure(client_proxy)
data_management.configure(client_proxy)
womens_health.configure(client_proxy)
nutrition.configure(client_proxy)
workout_builders.configure(client_proxy)
courses.configure(client_proxy)
activity_analysis.configure(client_proxy)

def init_user_api(email, password, tokenstore_dir, tokens_base64=None):
    """Inicializa cliente Garmin Connect para um usuario especifico."""
    expanded_tokenstore = os.path.expanduser(tokenstore_dir)
    os.makedirs(expanded_tokenstore, exist_ok=True)
    token_json_path = os.path.join(expanded_tokenstore, "garmin_tokens.json")

    if tokens_base64:
        try:
            decoded = base64.b64decode(tokens_base64.strip()).decode("utf-8")
            with open(token_json_path, "w", encoding="utf-8") as f:
                f.write(decoded)
            print(f"Token base64 gravado em {token_json_path}", file=sys.stderr)
        except Exception as e:
            print(f"Erro ao decodificar base64: {e}", file=sys.stderr)

    try:
        print(f"Tentando login Garmin via tokens em '{tokenstore_dir}'...", file=sys.stderr)
        garmin = Garmin()
        garmin.login(expanded_tokenstore)
        print(f"Login Garmin realizado com sucesso para '{tokenstore_dir}'!", file=sys.stderr)
        return garmin
    except Exception as e:
        print(f"Aviso no login por tokens em '{tokenstore_dir}': {e}", file=sys.stderr)

    if email and password:
        try:
            print(f"Tentando login via email/senha para '{email}'...", file=sys.stderr)
            garmin = Garmin(email=email, password=password)
            garmin.login()
            garmin.client.dump(expanded_tokenstore)
            print(f"Login via email/senha realizado e tokens salvos em '{tokenstore_dir}'!", file=sys.stderr)
            return garmin
        except Exception as e:
            print(f"Erro no login via email/senha para '{email}': {e}", file=sys.stderr)

    print(f"AVISO: Cliente Garmin nao autenticado para '{tokenstore_dir}'. Servidor rodara normalmente.", file=sys.stderr)
    return None

def wrap_app_tools(app, user_client):
    """Wraps all tool functions on the app to set the active client context during execution."""
    for tool_name, tool in app._tool_manager._tools.items():
        original_fn = tool.fn
        if inspect.iscoroutinefunction(original_fn):
            @functools.wraps(original_fn)
            async def wrapped_async(*args, **kwargs):
                token = current_garmin_client.set(user_client)
                try:
                    return await original_fn(*args, **kwargs)
                finally:
                    current_garmin_client.reset(token)
            tool.fn = wrapped_async
        else:
            @functools.wraps(original_fn)
            def wrapped_sync(*args, **kwargs):
                token = current_garmin_client.set(user_client)
                try:
                    return original_fn(*args, **kwargs)
                finally:
                    current_garmin_client.reset(token)
            tool.fn = wrapped_sync

def create_user_mcp_app(user_name, email, password, tokenstore_dir, tokens_base64=None):
    """Cria e configura o FastMCP app isolado para um usuario."""
    user_client = init_user_api(email, password, tokenstore_dir, tokens_base64)

    app = FastMCP(f"Garmin Connect - {user_name}")
    app.settings.transport_security.enable_dns_rebinding_protection = False
    app.settings.transport_security.allowed_hosts = ["*"]
    app.settings.mount_path = f"/{user_name.lower()}"

    # Registrar todas as ferramentas e recursos
    app = activity_management.register_tools(app)
    app = health_wellness.register_tools(app)
    app = user_profile.register_tools(app)
    app = devices.register_tools(app)
    app = gear_management.register_tools(app)
    app = weight_management.register_tools(app)
    app = challenges.register_tools(app)
    app = training.register_tools(app)
    app = workouts.register_tools(app)
    app = data_management.register_tools(app)
    app = womens_health.register_tools(app)
    app = nutrition.register_tools(app)
    app = workout_builders.register_tools(app)
    app = courses.register_tools(app)
    app = activity_analysis.register_tools(app)
    app = workout_templates.register_resources(app)

    # Wrap tool functions to route the global client proxy dynamically to the specific user client
    wrap_app_tools(app, user_client)

    return app.sse_app()

def get_master_app():
    """Cria a aplicacao mestre Starlette unindo Pedro e Laura."""
    pedro_email = os.getenv("PEDRO_EMAIL") or os.getenv("GARMIN_EMAIL") or "pedrocastrodias@gmail.com"
    pedro_pass = os.getenv("PEDRO_PASSWORD") or os.getenv("GARMIN_PASSWORD") or "Pel-171593"
    pedro_b64 = os.getenv("PEDRO_TOKENS_BASE64")

    laura_email = os.getenv("LAURA_EMAIL") or "laurasisdelli@gmail.com"
    laura_pass = os.getenv("LAURA_PASSWORD") or "Hsc#180723"
    laura_b64 = os.getenv("LAURA_TOKENS_BASE64")

    pedro_tokenstore = os.getenv("PEDRO_TOKENSTORE") or "~/.garminconnect"
    laura_tokenstore = os.getenv("LAURA_TOKENSTORE") or "~/.garminconnect_laura"

    pedro_sse = create_user_mcp_app("Pedro", pedro_email, pedro_pass, pedro_tokenstore, pedro_b64)
    laura_sse = create_user_mcp_app("Laura", laura_email, laura_pass, laura_tokenstore, laura_b64)

    from starlette.middleware.base import BaseHTTPMiddleware

    class PreventBufferingMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            response = await call_next(request)
            response.headers["Cache-Control"] = "no-cache, no-transform"
            response.headers["X-Accel-Buffering"] = "no"
            response.headers["Connection"] = "keep-alive"
            return response

    routes = [
        Route("/", endpoint=lambda r: PlainTextResponse("Servidor Garmin MCP Multi-Usuario (Pedro & Laura) ONLINE 24/7!")),
        Mount("/pedrogarminsolucao123", app=pedro_sse),
        Mount("/lauragarminsolucao123", app=laura_sse),
        # Alias simples para facilidade de uso
        Mount("/pedro", app=pedro_sse),
        Mount("/laura", app=laura_sse),
    ]

    master_app = Starlette(routes=routes)
    master_app.add_middleware(PreventBufferingMiddleware)
    return master_app

master_app = get_master_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Iniciando Servidor Garmin MCP Multi-Usuario na porta {port}...", file=sys.stderr)
    uvicorn.run(
        master_app,
        host=host,
        port=port,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
