from mcp.server.fastmcp import FastMCP
import requests
import os

mcp = FastMCP("Mail-Echo", host="0.0.0.0", port=8002)

INTERNAL_API_URL = "http://app:8010"
if os.getenv("IS_LOCAL") == "1":
    INTERNAL_API_URL = "http://localhost:8010"


@mcp.tool()
async def sende_mail(email: str, ansprechpartner: str, firmenname: str, stufe: int) -> dict:
    """Sendet eine Mail an einen Lead. stufe: 1=Erstanschreiben, 2=Follow-up, 3=Letzte Nachricht."""
    response = requests.post(f"{INTERNAL_API_URL}/api/mailing/sende", json={
        "email": email,
        "ansprechpartner": ansprechpartner,
        "firmenname": firmenname,
        "stufe": stufe
    })
    try:
        return response.json()
    except:
        return {"error": response.text}

@mcp.tool()
async def hole_antworten() -> dict:
    """IMAP: neue Antworten holen und in DB speichern"""
    response = requests.post(f"{INTERNAL_API_URL}/api/posteingang/fetch")
    try:
        return response.json()
    except:
        return {"error": response.text}

@mcp.tool()
async def lese_posteingang() -> list:
    """Gibt unverarbeitete Antworten zurück (mit Firmenname und Stufe)"""
    response = requests.get(f"{INTERNAL_API_URL}/api/posteingang/")
    try:
        return response.json()
    except:
        return [{"error": response.text}]

@mcp.tool()
async def auswerten(mail_id: int, entscheidung: str, notiz: str) -> dict:
    """Klassifiziert eine Antwort im Posteingang als verarbeitet"""
    response = requests.post(f"{INTERNAL_API_URL}/api/posteingang/{mail_id}/auswerten", json={
        "entscheidung": entscheidung,
        "notiz": notiz
    })
    try:
        return response.json()
    except:
        return {"error": response.text}

@mcp.tool()
async def kampagnen_stats() -> dict:
    """Übersicht: gesendete Mails pro Stufe, Öffnungen, Abmeldungen, Antworten"""
    response = requests.get(f"{INTERNAL_API_URL}/api/stats/")
    try:
        return response.json()
    except:
        return {"error": response.text}

@mcp.tool()
async def offnungen() -> list:
    """Zeigt alle Leads die eine Mail geöffnet haben (mit Zeitstempel und Stufe)"""
    response = requests.get(f"{INTERNAL_API_URL}/api/stats/offnungen")
    try:
        return response.json()
    except:
        return [{"error": response.text}]

@mcp.tool()
async def lese_unterlagen_anfragen() -> list:
    """
    Gibt alle Unterlagen-Anfragen zurück die noch nicht in PROD verarbeitet wurden.
    Felder: id, tracking_uuid, email, firmenname, ansprechpartner, geklickt_am.
    Mit email+firmenname den Lead in PROD per leads_liste() oder lead_lesen() identifizieren.
    Nach Verarbeitung: unterlagen_bestaetigen(id) aufrufen.
    """
    response = requests.get(f"{INTERNAL_API_URL}/api/hooks/unterlagen/offen")
    try:
        return response.json()
    except:
        return [{"error": response.text}]

@mcp.tool()
async def unterlagen_bestaetigen(hook_id: int) -> dict:
    """Markiert eine Unterlagen-Anfrage als in PROD verarbeitet (hook_id aus lese_unterlagen_anfragen)"""
    response = requests.post(f"{INTERNAL_API_URL}/api/hooks/unterlagen/{hook_id}/bestaetigen")
    try:
        return response.json()
    except:
        return {"error": response.text}

@mcp.tool()
async def lese_interesse_klicks() -> list:
    """
    Gibt alle Interesse-Klicks zurück die noch nicht in PROD verarbeitet wurden.
    Felder: id, tracking_uuid, email, firmenname, ansprechpartner, geklickt_am.
    Mit email+firmenname den Lead in PROD per leads_liste() oder lead_lesen() identifizieren.
    Nach Verarbeitung: interesse_bestaetigen(id) aufrufen.
    """
    response = requests.get(f"{INTERNAL_API_URL}/api/hooks/interesse/offen")
    try:
        return response.json()
    except:
        return [{"error": response.text}]

@mcp.tool()
async def interesse_bestaetigen(hook_id: int) -> dict:
    """Markiert einen Interesse-Klick als in PROD verarbeitet (hook_id aus lese_interesse_klicks)"""
    response = requests.post(f"{INTERNAL_API_URL}/api/hooks/interesse/{hook_id}/bestaetigen")
    try:
        return response.json()
    except:
        return {"error": response.text}

@mcp.tool()
async def lese_abmeldungen() -> list:
    """
    Gibt alle Abmeldungen zurück die noch nicht in PROD nachgepflegt wurden.
    Felder: id, tracking_uuid, email, firmenname, ansprechpartner, geklickt_am.
    Nach Verarbeitung: abmeldung_bestaetigen(id) aufrufen.
    """
    response = requests.get(f"{INTERNAL_API_URL}/api/hooks/abmelden/offen")
    try:
        return response.json()
    except:
        return [{"error": response.text}]

@mcp.tool()
async def abmeldung_bestaetigen(abmeldung_id: int) -> dict:
    """Markiert eine Abmeldung als in PROD nachgepflegt (abmeldung_id aus lese_abmeldungen)"""
    response = requests.post(f"{INTERNAL_API_URL}/api/hooks/abmelden/{abmeldung_id}/bestaetigen")
    try:
        return response.json()
    except:
        return {"error": response.text}


if __name__ == "__main__":
    mcp.run(transport='sse')
