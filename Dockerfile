FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias de compilar se necessario
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ libffi-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY garmin_mcp_server/src /app/src

ENV PYTHONPATH=/app/src
ENV PORT=8000
ENV HOST=0.0.0.0

EXPOSE 8000

CMD ["python", "src/garmin_mcp/server_multi.py"]
