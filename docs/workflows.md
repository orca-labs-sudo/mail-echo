# Mail-Echo — Workflows

Vollständige Prozessbeschreibung. Jeder Workflow hat: Eingang → Verarbeitung → Ausgang → Trigger.

---

## WORKFLOW 1 — Lead-Import (CSV)

```
Eingang:  CSV-Datei (Pflichtfeld: email)
          Format: firmenname;email;ansprechpartner;telefon;branche
Verarbeitung:
  → Duplikat-Check per E-Mail (bereits in DB → überspringen)
  → Fehlende Felder: leer lassen, kein Fehler
  → Alle neuen Leads: Status "neu", Sequenz-Schritt 0
Ausgang:  {importiert: 632, duplikate: 18, fehler: 0}
Trigger:  Manueller Upload via Web UI (Button)
          ODER Claude MCP-Tool: import_csv(dateiinhalt)
```

**Hinweis:** Leads kommen als CSV die Claude auf Zuruf erstellt.
Kein eigener Scraper — Claude recherchiert und liefert CSV.

---

## WORKFLOW 2 — Template-Verwaltung (Spielplatz)

```
Eingang:  User öffnet https://mail-echo.techniker0.me/templates
Verarbeitung:
  → Liste aller Templates (Name, Stufe 1/2/3, letzte Änderung)
  → Klick "Neu" / "Bearbeiten":
       Betreff-Feld (Text)
       Textkörper (Textarea)
       Placeholder-Buttons: [+Firma] [+Ansprechpartner]
         → Klick fügt [FIRMA] / [ANSPRECHPARTNER] an Cursor-Position ein
  → "Vorschau" Button:
       Service rendert mit Musterdaten (Mustermann GmbH, Hr. Müller)
       → echte HTML-Mail öffnet im Browser-Tab
       → exakt was Empfänger sieht
  → "Freigeben" → Template nutzbar für Claude
Ausgang:  Template in DB, freigegeben
Trigger:  Manuell durch User
```

**Wichtig:** Claude schreibt KEINEN Mailtext. Nur der User schreibt Templates.
Claude füllt nur [FIRMA] und [ANSPRECHPARTNER] ein.

---

## WORKFLOW 3 — Sequenz-Planung

```
Eingang:  Claude fragt: tagesplanung()
Verarbeitung:
  → Service berechnet fällige Mails:
       Stufe 1: status="neu", noch keine Mail gesendet
       Stufe 2: mail_1_gesendet_am < heute - 6 Tage
                UND status NOT IN ('geantwortet','abgemeldet','kein_interesse')
       Stufe 3: mail_2_gesendet_am < heute - 7 Tage
                UND status NOT IN (s.o.)
  → Gibt zurück: {stufe_1: 45, stufe_2: 12, stufe_3: 8}
Ausgang:  Claude entscheidet wie viele er heute sendet
Trigger:  Claude MCP-Tool
```

---

## WORKFLOW 4 — Mailversand (Batch)

```
Eingang:  Claude: sende_batch(stufe=1, limit=50)
Verarbeitung:
  → Service holt N Leads die diese Stufe noch nicht haben
  → Für jeden Lead:
       Template laden (Stufe X)
       [FIRMA] → lead.firmenname
       [ANSPRECHPARTNER] → lead.ansprechpartner (Fallback: "Damen und Herren")
       Tracking-Pixel einbetten: <img src="https://mail-echo.techniker0.me/track/{uuid}/open.gif">
       Abmeldelink einbetten: https://mail-echo.techniker0.me/unsubscribe/{lead_uuid}
       Via IONOS SMTP senden (vertrieb@awr24.de)
       SMTP Message-ID speichern (für Reply-Matching)
       Versand-Log Eintrag anlegen
       Lead-Status aktualisieren: "mail_X_gesendet", Zeitstempel
  → Gibt zurück: {gesendet: 50, fehler: 0, fehlgeschlagen: []}
Ausgang:  Mails draußen, alle geloggt
Trigger:  Claude MCP-Tool (nie automatisch)
Limit:    Service verweigert > 100 Mails pro Aufruf (hart codiert)
```

---

## WORKFLOW 5 — Öffnungs-Tracking (passiv)

```
Eingang:  Empfänger öffnet Mail → Mail-Client lädt Pixel
Verarbeitung:
  → GET /track/{uuid}/open.gif
  → UUID → Versand-Log Eintrag suchen
  → Erstes Mal: geoeffnet_am = jetzt, Lead-Status ergänzen
  → Folgeaufrufe: ignorieren
  → Antwort: 1x1 transparentes GIF (43 Bytes)
Ausgang:  Öffnung geloggt
Trigger:  Vollautomatisch, kein Eingriff
```

**Einschränkung:** Gmail, Outlook 365 etc. blockieren Pixel zunehmend (Apple Mail Privacy).
Öffnungsrate = Indikator, kein exakter Wert. Antwort-Rate ist verlässlicher.

---

## WORKFLOW 6 — Posteingang abholen (IMAP)

```
Eingang:  Claude: hole_antworten()
Verarbeitung:
  → IMAP-Login: vertrieb@awr24.de (IONOS, Port 993 SSL)
  → Sucht UNSEEN Mails im Posteingang
  → Für jede Mail:
       In-Reply-To Header → matched auf gespeicherte Message-IDs
       → Lead identifiziert (oder "unbekannt" wenn kein Match)
       Plain-Text Body extrahieren (KEIN HTML an Claude)
       IMAP-UID speichern (Duplikat-Schutz)
       Mail als SEEN markieren
       Posteingang-Eintrag in DB anlegen
  → Gibt zurück: {neue_antworten: 5, nicht_zugeordnet: 1}
Ausgang:  Antworten in DB, bereit zur Auswertung
Trigger:  Claude MCP-Tool (on-demand, kein Cronjob in Phase 1)
```

---

## WORKFLOW 7 — Antwort-Auswertung (Claude)

```
Eingang:  Claude: lese_posteingang()
          → Service gibt unverarbeitete Einträge zurück
            (id, firma, betreff, plain_text, empfangen_am)
Verarbeitung:
  → Claude liest jeden Plain-Text und entscheidet:
       "Bitte rufen Sie mich an"   → "kontakt_erbeten"
       "Termin möglich"            → "interessiert"
       "Kein Interesse"            → "ablehnung"
       "Im Urlaub bis..."          → "abwesenheit" + Notiz
       "Haben eigene Lösung"       → "ablehnung"
       Rückfrage zum Angebot       → "interessiert"
  → Claude: auswerten(mail_id, entscheidung, notiz)
  → Service: Lead-Status aktualisiert, Sequenz gestoppt
Ausgang:  Alle Antworten klassifiziert, Leads sortiert
Trigger:  Claude (direkt nach hole_antworten)
```

---

## WORKFLOW 8 — Abmeldung (Unsubscribe)

```
Eingang:  Empfänger klickt Abmeldelink in Mail
Verarbeitung:
  → GET /unsubscribe/{lead_uuid}
  → Lead-Status: "abgemeldet"
  → Gesperrt: Service prüft vor jedem Versand
  → HTML-Bestätigungsseite: "Sie wurden erfolgreich abgemeldet"
Ausgang:  Lead permanent gesperrt
Trigger:  Vollautomatisch
Pflicht:  §7 UWG — muss in JEDER Mail enthalten sein
```

---

## WORKFLOW 9 — Reporting

```
Via Browser (https://mail-echo.techniker0.me/stats):
  → Gesamtübersicht: Leads, Versendete Mails, Öffnungsrate,
    Antwortrate, Abmeldungen, Interessenten, Konversionen

Via Claude MCP (kampagnen_stats()):
  → Kompakte Zahlen für Entscheidungen
  → Beispiel: "650 Leads: 312 Mail 1, 89 geöffnet (28%),
    23 geantwortet (7%), 8 interessiert, 4 abgemeldet"
```

---

## Lead-Status Lifecycle

```
neu
 │
 ├─→ mail_1_gesendet (Tag 0)
 │       │
 │       ├─→ mail_2_gesendet (Tag 6, falls keine Antwort)
 │       │       │
 │       │       ├─→ mail_3_gesendet (Tag 13, falls keine Antwort)
 │       │       │       │
 │       │       │       └─→ inaktiv
 │       │       │
 │       │       └─→ geantwortet ──────────────────────┐
 │       │                                             │
 │       └─→ geantwortet ────────────────────────────── │
 │                                                     │
 └─────────────────────────────────────────────────────┘
                                                       ▼
                                              interessiert
                                              kontakt_erbeten
                                              ablehnung
                                              abwesenheit

abgemeldet  → jederzeit möglich, sofort permanent gesperrt
```
