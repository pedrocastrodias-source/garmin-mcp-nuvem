import os
import sys
import base64
import uvicorn
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

def create_user_mcp_app(user_name, email, password, tokenstore_dir, tokens_base64=None):
    """Cria e configura o FastMCP app isolado para um usuario."""
    garmin_client = init_user_api(email, password, tokenstore_dir, tokens_base64)

    # Configurar modulos com o cliente do usuario
    activity_management.configure(garmin_client)
    health_wellness.configure(garmin_client)
    user_profile.configure(garmin_client)
    devices.configure(garmin_client)
    gear_management.configure(garmin_client)
    weight_management.configure(garmin_client)
    challenges.configure(garmin_client)
    training.configure(garmin_client)
    workouts.configure(garmin_client)
    data_management.configure(garmin_client)
    womens_health.configure(garmin_client)
    nutrition.configure(garmin_client)
    workout_builders.configure(garmin_client)
    courses.configure(garmin_client)
    activity_analysis.configure(garmin_client)

    app = FastMCP(f"Garmin Connect - {user_name}")
    app.settings.transport_security.enable_dns_rebinding_protection = False
    app.settings.transport_security.allowed_hosts = ["*"]

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

    routes = [
        Route("/", endpoint=lambda r: PlainTextResponse("Servidor Garmin MCP Multi-Usuario (Pedro & Laura) ONLINE 24/7!")),
        Mount("/pedrogarminsolucao123", app=pedro_sse),
        Mount("/lauragarminsolucao123", app=laura_sse),
        # Alias simples para facilidade de uso
        Mount("/pedro", app=pedro_sse),
        Mount("/laura", app=laura_sse),
    ]

    return Starlette(routes=routes)

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
