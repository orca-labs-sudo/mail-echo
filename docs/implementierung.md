# Mail-Echo — Implementierungsanleitung

Konkrete Bauanleitung: Dateistruktur, DB-Schema, API-Endpunkte, MCP-Tools.
Reihenfolge einhalten — jeder Schritt baut auf dem vorherigen auf.

---

## Projektstruktur

```
mail-echo/
├── CLAUDE.md
├── .env                        ← Credentials (gitignore!)
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
│
├── app/
│   ├── main.py                 ← FastAPI App + CORS + Routers einbinden
│   ├── config.py               ← Settings aus .env laden
│   ├── database.py             ← SQLite Verbindung, Tabellen anlegen
│   │
│   ├── models.py               ← SQLAlchemy Modelle (alle Tabellen)
│   │
│   ├── routers/
│   │   ├── leads.py            ← CSV-Import, Lead-Liste
│   │   ├── templates.py        ← Template CRUD
│   │   ├── mailing.py          ← Batch-Versand, Tagesplanung
│   │   ├── posteingang.py      ← IMAP-Fetch, Auswerten
│   │   ├── tracking.py         ← Pixel-Endpoint, Unsubscribe
│   │   └── stats.py            ← Reporting
│   │
│   ├── services/
│   │   ├── smtp_service.py     ← IONOS SMTP Verbindung, Mail senden
│   │   ├── imap_service.py     ← IONOS IMAP, Mails holen, Reply-Matching
│   │   ├── template_service.py ← Platzhalter ersetzen, HTML rendern (Jinja2)
│   │   └── sequenz_service.py  ← Fällige Mails berechnen (Stufe 1/2/3)
│   │
│   └── mcp_server.py           ← FastMCP Server, alle Tools definiert
│
├── ui/                         ← Spielplatz Web UI
│   ├── templates/              ← Jinja2 HTML Templates
│   │   ├── base.html
│   │   ├── leads.html
│   │   ├── templates_list.html
│   │   ├── template_edit.html
│   │   ├── template_preview.html
│   │   ├── stats.html
│   │   └── unsubscribe.html
│   └── static/
│       └── style.css
│
├── nginx/
│   └── nginx.mail-echo.conf
│
└── docs/
    ├── workflows.md
    ├── entscheidungen.md
    └── implementierung.md      ← diese Datei
```

---

## Schritt 1 — Datenbank-Schema (`app/models.py`)

### Tabelle: `leads`
```
id              INTEGER PRIMARY KEY AUTOINCREMENT
firmenname      TEXT
email           TEXT UNIQUE NOT NULL
ansprechpartner TEXT
telefon         TEXT
branche         TEXT
status          TEXT DEFAULT 'neu'
                  Werte: neu | mail_1_gesendet | mail_2_gesendet |
                         mail_3_gesendet | geantwortet | interessiert |
                         kontakt_erbeten | ablehnung | abwesenheit |
                         inaktiv | abgemeldet
mail_1_gesendet_am  DATETIME
mail_2_gesendet_am  DATETIME
mail_3_gesendet_am  DATETIME
abgemeldet_am   DATETIME
erstellt_am     DATETIME DEFAULT CURRENT_TIMESTAMP
```

### Tabelle: `mail_templates`
```
id              INTEGER PRIMARY KEY AUTOINCREMENT
name            TEXT NOT NULL
stufe           INTEGER NOT NULL   (1, 2 oder 3)
betreff         TEXT NOT NULL
html_body       TEXT NOT NULL      (Jinja2 Template mit [FIRMA] / [ANSPRECHPARTNER])
freigegeben     BOOLEAN DEFAULT 0  (nur freigegebene Templates nutzt Claude)
erstellt_am     DATETIME DEFAULT CURRENT_TIMESTAMP
geaendert_am    DATETIME
```

### Tabelle: `versand_log`
```
id              INTEGER PRIMARY KEY AUTOINCREMENT
lead_id         INTEGER REFERENCES leads(id)
template_id     INTEGER REFERENCES mail_templates(id)
stufe           INTEGER
tracking_uuid   TEXT UNIQUE NOT NULL   (UUID4, für Pixel)
smtp_message_id TEXT                   (für Reply-Matching)
gesendet_am     DATETIME DEFAULT CURRENT_TIMESTAMP
geoeffnet_am    DATETIME
```

### Tabelle: `posteingang`
```
id              INTEGER PRIMARY KEY AUTOINCREMENT
lead_id         INTEGER REFERENCES leads(id)   (NULL wenn kein Match)
versand_id      INTEGER REFERENCES versand_log(id)
imap_uid        TEXT UNIQUE NOT NULL
absender        TEXT
betreff         TEXT
plain_text      TEXT
empfangen_am    DATETIME
verarbeitet     BOOLEAN DEFAULT 0
ki_entscheidung TEXT    (interessiert|kontakt_erbeten|ablehnung|abwesenheit)
ki_notiz        TEXT
```

---

## Schritt 2 — Konfiguration (`app/config.py` + `.env`)

### `.env` Felder
```
# SMTP
SMTP_HOST=smtp.ionos.de
SMTP_PORT=587
SMTP_USER=vertrieb@awr24.de
SMTP_PASSWORD=...
SMTP_FROM=vertrieb@awr24.de

# IMAP
IMAP_HOST=imap.ionos.de
IMAP_PORT=993
IMAP_USER=vertrieb@awr24.de
IMAP_PASSWORD=...

# Service
BASE_URL=https://mail-echo.techniker0.me
SECRET_KEY=...           (für MCP-Authentifizierung)
MCP_PORT=8002
APP_PORT=8010

# DB
DATABASE_PATH=./mail_echo.db
```

---

## Schritt 3 — API-Endpunkte

### Leads (`/api/leads/`)

| Endpunkt | Methode | Funktion |
|---|---|---|
| `/api/leads/import` | POST | CSV-Datei hochladen, Bulk-Import |
| `/api/leads/` | GET | Liste mit Filter (status, stufe_faellig) |
| `/api/leads/{id}` | GET | Einzelner Lead |
| `/api/leads/{id}` | PATCH | Status manuell ändern |

**CSV-Import Response:**
```json
{"importiert": 632, "duplikate": 18, "fehler": 0, "fehlerliste": []}
```

### Templates (`/api/templates/`)

| Endpunkt | Methode | Funktion |
|---|---|---|
| `/api/templates/` | GET | Alle Templates |
| `/api/templates/` | POST | Neues Template anlegen |
| `/api/templates/{id}` | GET | Einzelnes Template |
| `/api/templates/{id}` | PUT | Template bearbeiten |
| `/api/templates/{id}/freigeben` | POST | Template für Claude freigeben |
| `/api/templates/{id}/vorschau` | GET | HTML-Render mit Musterdaten |

### Mailing (`/api/mailing/`)

| Endpunkt | Methode | Funktion |
|---|---|---|
| `/api/mailing/tagesplanung` | GET | Fällige Mails pro Stufe |
| `/api/mailing/batch` | POST | Batch senden `{stufe: 1, limit: 50}` |

**Batch-Response:**
```json
{"gesendet": 50, "fehler": 0, "fehlgeschlagen": []}
```

**Sicherheit:** Service verweigert `limit > 100` mit HTTP 400.

### Posteingang (`/api/posteingang/`)

| Endpunkt | Methode | Funktion |
|---|---|---|
| `/api/posteingang/fetch` | POST | IMAP abholen → DB befüllen |
| `/api/posteingang/` | GET | Unverarbeitete Einträge |
| `/api/posteingang/{id}/auswerten` | POST | `{entscheidung, notiz}` speichern |

### Tracking (öffentlich, kein Auth)

| Endpunkt | Methode | Funktion |
|---|---|---|
| `/track/{uuid}/open.gif` | GET | Tracking-Pixel (1x1 GIF) |
| `/unsubscribe/{lead_uuid}` | GET | Abmeldung + Bestätigungsseite |

### Stats (`/api/stats/`)

| Endpunkt | Methode | Funktion |
|---|---|---|
| `/api/stats/` | GET | Gesamtübersicht als JSON |

---

## Schritt 4 — MCP-Tools (`app/mcp_server.py`)

Alle Tools rufen intern die FastAPI-Endpunkte auf (oder direkt Services).
Transport: SSE (wie bestehender mcp_server.py in Kanzlei_V3).

```python
@mcp.tool()
async def tagesplanung() -> dict:
    """Zeigt fällige Mails pro Stufe (1/2/3)"""

@mcp.tool()
async def sende_batch(stufe: int, limit: int) -> dict:
    """Sendet Batch-Mails an fällige Leads. Max 100 pro Aufruf."""

@mcp.tool()
async def hole_antworten() -> dict:
    """IMAP: neue Antworten holen und in DB speichern"""

@mcp.tool()
async def lese_posteingang() -> list:
    """Gibt unverarbeitete Posteingang-Einträge zurück (plain text only)"""

@mcp.tool()
async def auswerten(mail_id: int, entscheidung: str, notiz: str) -> dict:
    """Klassifiziert eine Antwort und aktualisiert Lead-Status"""

@mcp.tool()
async def kampagnen_stats() -> dict:
    """Übersicht: gesendet, geöffnet, geantwortet, Konversionen"""
```

**MCP-Authentifizierung:** Bearer Token (SECRET_KEY aus .env).
Nur Claude.ai mit konfiguriertem Token hat Zugriff.

---

## Schritt 5 — Template-Rendering (`app/services/template_service.py`)

```python
# Platzhalter ersetzen
text = template.html_body
text = text.replace("[FIRMA]", lead.firmenname or "Ihrem Unternehmen")
text = text.replace("[ANSPRECHPARTNER]", lead.ansprechpartner or "Damen und Herren")

# Tracking-Pixel + Abmeldelink einbetten
pixel_url = f"{BASE_URL}/track/{tracking_uuid}/open.gif"
unsub_url = f"{BASE_URL}/unsubscribe/{lead_uuid}"

# In HTML-Mail-Wrapper einbetten (Jinja2)
html = jinja_env.get_template("mail_wrapper.html").render(
    content=text,
    pixel_url=pixel_url,
    unsub_url=unsub_url,
)
```

---

## Schritt 6 — NGINX (`nginx/nginx.mail-echo.conf`)

```nginx
server {
    listen 80;
    server_name mail-echo.techniker0.me;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name mail-echo.techniker0.me;

    ssl_certificate /etc/ssl/kanzlei/fullchain.pem;
    ssl_certificate_key /etc/ssl/kanzlei/techniker0.key;

    location / {
        proxy_pass http://mail-echo:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /mcp {
        proxy_pass http://mail-echo:8002;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_read_timeout 3600s;
    }
}
```

---

## Reihenfolge der Implementierung

```
1. Projektstruktur anlegen (Ordner, leere Dateien)
2. requirements.txt + Dockerfile + docker-compose.yml
3. config.py + .env.example
4. database.py + models.py (SQLite Schema)
5. smtp_service.py (SMTP-Verbindung testen)
6. imap_service.py (IMAP-Verbindung testen)
7. template_service.py (Platzhalter, HTML-Wrapper)
8. sequenz_service.py (fällige Leads berechnen)
9. Router: leads.py (CSV-Import)
10. Router: templates.py (CRUD + Vorschau)
11. Router: mailing.py (Batch-Versand)
12. Router: tracking.py (Pixel + Unsubscribe)
13. Router: posteingang.py (IMAP-Fetch + Auswerten)
14. Router: stats.py
15. main.py (alles zusammenführen)
16. mcp_server.py (MCP-Tools)
17. Web UI (HTML/CSS Spielplatz)
18. NGINX-Config
19. Docker-Deploy auf techniker0.me
20. Test End-to-End (siehe unten)
```

---

## End-to-End Test

```
1. CSV mit 3 Test-Leads hochladen
   → /leads zeigt 3 Einträge, Status "neu"

2. Template anlegen (Stufe 1), freigeben
   → /templates/1/vorschau zeigt HTML-Mail mit Musterdaten

3. Claude: tagesplanung() → {stufe_1: 3}
4. Claude: sende_batch(stufe=1, limit=3)
   → 3 Mails im Testpostfach, Pixel-URL im HTML-Quellcode sichtbar

5. Mail öffnen → Pixel lädt
   → versand_log.geoeffnet_am gesetzt

6. Auf Mail antworten (Testpostfach → vertrieb@awr24.de)
7. Claude: hole_antworten() → {neue_antworten: 1}
8. Claude: lese_posteingang() → Mail-Text zurück
9. Claude: auswerten(mail_id=1, entscheidung="interessiert", notiz="Test")
   → Lead Status "interessiert"

10. /unsubscribe/{lead_uuid} aufrufen
    → Bestätigungsseite, Lead Status "abgemeldet"

11. Claude: kampagnen_stats() → korrekte Zahlen
```
