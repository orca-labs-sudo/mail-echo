# CLAUDE.md — Mail-Echo

> Projektkontext für Claude Code / Claude Desktop.
> Wird automatisch beim Start eingelesen.

---

## Was ist Mail-Echo?

**Mail-Echo** ist der Outbound-Vertriebsservice von AWR24.
AWR24 ist eine Verkehrsrechtskanzlei die kostenloses Unfallmanagement für Fuhrpark-Unternehmen anbietet (Pflegedienste, Speditionen, LKW-Subunternehmer). Die gegnerische Versicherung trägt alle Kosten — das Produkt verkauft sich selbst, wenn die richtigen Leute erreicht werden.

**Ziel:** 30 neue Fälle/Monat durch automatisierten, personalisierten Outbound-Mailversand.

**Wichtig:** Mail-Echo ist ein komplett eigenständiger Service. Keine Integration in die Kanzlei-App. Keine Verbindung zu Loki. Läuft isoliert.

---

## Tech-Stack

| Layer | Technologie |
|---|---|
| API | Python FastAPI |
| MCP | FastMCP (SSE-Transport) |
| Datenbank | SQLite (Phase 1) |
| Template-Rendering | Jinja2 |
| SMTP / IMAP | smtplib / imaplib (Standard-Library) |
| Web UI | Einfaches HTML/CSS (kein React) |
| Container | Docker |
| Reverse Proxy | NGINX (auf techniker0.me) |

---

## Infrastruktur

| Was | Wert |
|---|---|
| Server | techniker0.me |
| Subdomain | mail-echo.techniker0.me |
| Container | `mail-echo` |
| NGINX-Config | `nginx/nginx.mail-echo.conf` |
| SMTP | info@awr24-service.de (IONOS, Port 587) |
| IMAP | info@awr24-service.de (IONOS, Port 993) |

---

## Architektur

```
Claude.ai (extern)
    │
    │ MCP (FastMCP, SSE)
    ▼
Mail-Echo Service (techniker0.me)
    ├── REST API        → MCP-Tools rufen hier an
    ├── Web UI          → Spielplatz (Browser, KEIN Claude)
    ├── SQLite DB       → Templates, Versand-Log, Posteingang
    ├── SMTP            → info@awr24-service.de (Ausgang)
    └── IMAP            → info@awr24-service.de (Eingang)

Kanban/CRM (getrennt):
    Claude → MCP → ycnex.de Kanzlei-App (VertriebsLead)
```

Mail-Echo speichert KEINE Leads. Leads leben in der Kanzlei-App auf ycnex.de.
Mail-Echo speichert nur: Templates, Versand-Log, Posteingang-Einträge.

---

## Was Claude steuert (MCP-Tools)

| Tool | Funktion |
|---|---|
| `tagesplanung()` | Zeigt fällige Mails (Stufe 1/2/3) |
| `sende_batch(stufe, limit)` | Sendet Batch an fällige Leads |
| `hole_antworten()` | IMAP → neue Antworten in DB speichern |
| `lese_posteingang()` | Unverarbeitete Antworten zurückgeben |
| `auswerten(mail_id, entscheidung, notiz)` | Antwort klassifizieren |
| `kampagnen_stats()` | Übersicht: gesendet, geöffnet, geantwortet |

---

## Mail-Sequenz

3 Mails pro Lead, Abstand je 6-7 Tage:

```
Tag  0: Mail 1 — Erstanschreiben
Tag  6: Mail 2 — Follow-up (nur wenn keine Antwort)
Tag 13: Mail 3 — Letzte Nachricht (nur wenn keine Antwort)
─────────────────────────────────────────────────
Danach: Lead → "inaktiv"
```

Max 100 Mails/Tag (Service-seitig erzwungen).

---

## Templates

Nur 2 Platzhalter:
- `[FIRMA]` → Firmenname des Leads
- `[ANSPRECHPARTNER]` → Ansprechpartner (Fallback: "Damen und Herren")

Templates werden im Web UI (Spielplatz) erstellt und als HTML-Vorschau getestet.
Claude schreibt keinen Mailtext — nur der User schreibt Templates.
Claude fügt nur Platzhalter ein und sendet ab.

---

## Lead-Status Lifecycle

```
neu → mail_1_gesendet → mail_2_gesendet → mail_3_gesendet → inaktiv
                                                    ↓ (bei Antwort)
                                               geantwortet
                                                    ↓
                              interessiert / kontakt_erbeten / ablehnung / abwesenheit
abgemeldet (jederzeit, sofort gesperrt)
```

---

## Rechtliches

- Abmeldelink (`/unsubscribe/{uuid}`) in **jeder** Mail — Pflicht §7 UWG
- B2B Cold-Mail in Deutschland legal bei berechtigtem Interesse
- Kein DSGVO-Problem (nur Firmenadressen, keine Privatpersonen)

---

## Was NICHT gebaut wird

- Kein React-Frontend
- Keine Kanzlei-App-Integration
- Keine Loki-Erweiterung
- Keine externe Mail-Middleware (kein EmailEngine, kein Listmonk)
- Kein Scraper (Leads kommen als CSV von Claude auf Zuruf)

---

## Konventionen

- Sprache: Deutsch (Kommentare, Commits, Antworten)
- Kein Commit ohne explizite Erlaubnis
- SQLite DB: `mail_echo.db` im Projektroot (in .gitignore)
- Credentials: `.env` (in .gitignore)
- Kein Code ohne klare Aufgabe — Schritt für Schritt
