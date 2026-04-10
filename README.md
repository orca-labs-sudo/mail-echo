# Mail-Echo

Automated outbound mail service with reply tracking and MCP orchestration.

## Overview

Mail-Echo is a standalone outbound mail service controlled by Claude via MCP.
It handles personalized mail campaigns, open tracking, IMAP reply ingestion and automated lead classification.

## Features

- **3-step mail sequences** — Day 0 / Day 6 / Day 13 per lead
- **Open tracking** — pixel-based, automatic
- **Reply ingestion** — IMAP polling on demand
- **AI classification** — Claude reads replies and updates lead status
- **Spielplatz** — simple web UI for template management and preview
- **Unsubscribe** — one-click, §7 UWG compliant
- **MCP interface** — fully controlled by Claude.ai externally

## Tech Stack

- Python FastAPI
- FastMCP (SSE transport)
- SQLite
- Jinja2
- smtplib / imaplib
- Docker + NGINX

## Architecture

```
Claude.ai → MCP → Mail-Echo API → IONOS SMTP/IMAP
                       ↓
                   SQLite DB
              (templates, log, inbox)
```

Lead management (CRM/Kanban) lives separately in the main application.
Mail-Echo stores only: templates, send log, inbox entries.

## Setup

```bash
cp .env.example .env
# fill in SMTP/IMAP credentials and BASE_URL
docker compose up -d
```

## Documentation

- [Workflows](docs/workflows.md)
- [Architecture Decisions](docs/entscheidungen.md)
- [Implementation Guide](docs/implementierung.md)
