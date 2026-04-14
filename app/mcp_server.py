from mcp.server.fastmcp import FastMCP
from app.services.sequenz_service import berechne_faellige_leads
from app.database import SessionLocal
import requests
from app.config import SECRET_KEY
import os

mcp = FastMCP("Mail-Echo", host="0.0.0.0", port=8002)

# Interne Kommunikation auf den FastAPI Server im Docker-Netzwerk
INTERNAL_API_URL = "http://app:8010" 
if os.getenv("IS_LOCAL") == "1":
    INTERNAL_API_URL = "http://localhost:8010"

def get_db_session():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

@mcp.tool()
async def tagesplanung() -> dict:
    """Zeigt fällige Mails pro Stufe (1/2/3)"""
    db = get_db_session()
    return berechne_faellige_leads(db)

@mcp.tool()
async def sende_batch(stufe: int, limit: int) -> dict:
    """Sendet Batch-Mails an fällige Leads. Max 100 pro Aufruf."""
    response = requests.post(f"{INTERNAL_API_URL}/api/mailing/batch", json={"stufe": stufe, "limit": limit})
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
    """Gibt unverarbeitete Posteingang-Einträge zurück (plain text only)"""
    response = requests.get(f"{INTERNAL_API_URL}/api/posteingang/")
    try:
        return response.json()
    except:
        return [{"error": response.text}]

@mcp.tool()
async def auswerten(mail_id: int, entscheidung: str, notiz: str) -> dict:
    """Klassifiziert eine Antwort und aktualisiert Lead-Status"""
    response = requests.post(f"{INTERNAL_API_URL}/api/posteingang/{mail_id}/auswerten", json={"entscheidung": entscheidung, "notiz": notiz})
    try:
        return response.json()
    except:
        return {"error": response.text}

@mcp.tool()
async def kampagnen_stats() -> dict:
    """Übersicht: gesendet, geöffnet, geantwortet, Konversionen"""
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
async def lese_abmeldungen() -> list:
    """Gibt alle Abmeldungen zurück die noch nicht in PROD nachgepflegt wurden"""
    response = requests.get(f"{INTERNAL_API_URL}/api/leads/abmeldungen/offen")
    try:
        return response.json()
    except:
        return [{"error": response.text}]

@mcp.tool()
async def abmeldung_bestaetigen(lead_id: int) -> dict:
    """Markiert eine Abmeldung als in PROD verarbeitet (nach lead_aktualisieren in Vertrieb)"""
    response = requests.post(f"{INTERNAL_API_URL}/api/leads/{lead_id}/abmeldung-bestaetigen")
    try:
        return response.json()
    except:
        return {"error": response.text}

if __name__ == "__main__":
    mcp.run(transport='sse')
