FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# API Port
EXPOSE 8010
# MCP Port
EXPOSE 8002
