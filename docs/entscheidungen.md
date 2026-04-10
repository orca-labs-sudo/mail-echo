# Mail-Echo — Architektur-Entscheidungen

Alle getroffenen Entscheidungen mit Begründung. Nicht ohne Diskussion ändern.

---

## Grundsatz-Entscheidungen

| Thema | Entscheidung | Begründung |
|---|---|---|
| Architektur | Separater eigenständiger Service | Kanzlei-App bleibt unangetastet, Loki bleibt sauber |
| Orchestrator | Claude.ai extern via MCP | Kein DSGVO-Problem (Firmenadressen), kein Risiko für Kanzlei |
| Loki | Nicht involviert | Loki hat RAG, ki_memory, Buchhaltung kommt — nicht verschmutzen |
| Kanban/CRM | Kanzlei-App ycnex.de | VertriebsLead bereits vorhanden, nicht doppelt bauen |
| Lead-Speicher | ycnex.de (Kanzlei-App) | Mail-Echo speichert KEINE Leads |
| mcp_server.py | Abschalten | Sicherheitslücke ohne Verwendungszweck |

---

## Lead-Beschaffung

| Thema | Entscheidung | Begründung |
|---|---|---|
| Scraper | Kein eigener Scraper | Jede Webseite braucht individuelle Anpassung — zu wartungsintensiv |
| Lead-Quelle | Claude erstellt CSV auf Zuruf | Kosten (~$0.30/650 Leads) günstiger als Scraper-Entwicklung |
| Import | Manueller CSV-Upload per Button | Einfachste Lösung, kein Automatismus nötig |
| Pflichtfeld | Nur E-Mail | Alles andere optional — maximale Flexibilität beim Import |

---

## Mail-System

| Thema | Entscheidung | Begründung |
|---|---|---|
| SMTP | IONOS direkt (smtplib) | 0 Lizenzkosten, volle Kontrolle |
| IMAP | IONOS direkt (imaplib) | 0 Lizenzkosten, on-demand |
| Externe Tools | Kein EmailEngine, kein Listmonk | EmailEngine: $995/Jahr. Listmonk: falsches Paradigma (Newsletter statt 1:1) |
| Platzhalter | Nur [FIRMA] und [ANSPRECHPARTNER] | Einfach, fehlerresistent, deckt 90% der Personalisierung |
| Template-Inhalt | User schreibt, Claude sendet nur | Kanzlei — jeder Text muss geprüft sein |
| Sequenz | 3 Mails (Tag 0, 6, 13) | Branchenstandard B2B: 5-9% Response vs. 1-3% bei Einzelmail |
| Versand-Limit | Max 100/Tag, hard coded | IONOS Spam-Schutz, Zustellrate |

---

## Template-Verwaltung (Spielplatz)

| Thema | Entscheidung | Begründung |
|---|---|---|
| Editor | Eigene simple Web UI | Django Admin zu tief für externe KI-Zugriffe (Sicherheit) |
| Vorschau | Echter HTML-Render im Browser | Claude rendert schlecht — bekanntes Problem |
| Platzhalter-Input | Buttons über Textarea | Verhindert Tipp-Fehler in Platzhaltern |
| Claude schreibt Templates | NEIN | Kanzlei — Texte müssen vom Menschen geprüft und freigegeben werden |

---

## Infrastruktur

| Thema | Entscheidung | Begründung |
|---|---|---|
| Server | techniker0.me | SSL (Ionos Wildcard) + NGINX bereits vorhanden |
| x402 VPS | Nicht genutzt | Domain/SSL-Setup zu aufwändig |
| Subdomain | mail-echo.techniker0.me | Wildcard *.techniker0.me deckt das ab |
| DB | SQLite Phase 1 | Einfach, kein separater DB-Container nötig |
| Frontend | HTML/CSS, kein React | Spielplatz ist intern, kein komplexes UI nötig |

---

## KI-Kosten (Referenz)

| Aktion | Kosten |
|---|---|
| CSV erstellen (650 Leads) | ~$0.30 |
| 1 Posteingang-Auswertung (10 Mails) | ~$0.008 |
| 1 Kampagnen-Session gesamt | ~$0.015 |
| Monatlich bei 500 Mails + 100 Antworten | < $0.15 |
