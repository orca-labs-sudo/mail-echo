from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import KonfigurationEintrag
from app.services.smtp_service import test_smtp_verbindung
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.sql import func

router = APIRouter()

SMTP_KEYS = ["smtp_host", "smtp_port", "smtp_user", "smtp_password", "smtp_from"]
IMAP_KEYS = ["imap_host", "imap_port", "imap_user", "imap_password"]


def _lese_config(db: Session, keys: list) -> dict:
    eintraege = db.query(KonfigurationEintrag).filter(
        KonfigurationEintrag.schluessel.in_(keys)
    ).all()
    return {e.schluessel: e.wert for e in eintraege}


def _speichere_config(db: Session, daten: dict):
    for key, value in daten.items():
        eintrag = db.query(KonfigurationEintrag).filter(
            KonfigurationEintrag.schluessel == key
        ).first()
        if eintrag:
            eintrag.wert = value
            eintrag.geaendert_am = func.now()
        else:
            db.add(KonfigurationEintrag(schluessel=key, wert=value))
    db.commit()


@router.get("/smtp")
def lese_smtp(db: Session = Depends(get_db)):
    """SMTP-Config aus DB lesen (Passwort maskiert)."""
    from app.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_FROM
    defaults = {
        "smtp_host": SMTP_HOST,
        "smtp_port": str(SMTP_PORT),
        "smtp_user": SMTP_USER,
        "smtp_password": "",
        "smtp_from": SMTP_FROM,
    }
    db_config = _lese_config(db, SMTP_KEYS)
    merged = {**defaults, **{k: v for k, v in db_config.items() if v is not None}}
    # Passwort maskieren
    if merged.get("smtp_password"):
        merged["smtp_password_gesetzt"] = True
        merged["smtp_password"] = "••••••••"
    else:
        merged["smtp_password_gesetzt"] = False
    return merged


@router.get("/imap")
def lese_imap(db: Session = Depends(get_db)):
    """IMAP-Config aus DB lesen (Passwort maskiert)."""
    from app.config import IMAP_HOST, IMAP_PORT, IMAP_USER
    defaults = {
        "imap_host": IMAP_HOST,
        "imap_port": str(IMAP_PORT),
        "imap_user": IMAP_USER,
        "imap_password": "",
    }
    db_config = _lese_config(db, IMAP_KEYS)
    merged = {**defaults, **{k: v for k, v in db_config.items() if v is not None}}
    if merged.get("imap_password"):
        merged["imap_password_gesetzt"] = True
        merged["imap_password"] = "••••••••"
    else:
        merged["imap_password_gesetzt"] = False
    return merged


class SmtpConfig(BaseModel):
    smtp_host: str
    smtp_port: str
    smtp_user: str
    smtp_from: str
    smtp_password: Optional[str] = None  # leer = unverändert lassen


class ImapConfig(BaseModel):
    imap_host: str
    imap_port: str
    imap_user: str
    imap_password: Optional[str] = None


@router.post("/smtp")
def speichere_smtp(config: SmtpConfig, db: Session = Depends(get_db)):
    """SMTP-Config in DB speichern."""
    daten = {
        "smtp_host": config.smtp_host,
        "smtp_port": config.smtp_port,
        "smtp_user": config.smtp_user,
        "smtp_from": config.smtp_from,
    }
    # Passwort nur überschreiben wenn angegeben und nicht Maskierung
    if config.smtp_password and config.smtp_password != "••••••••":
        daten["smtp_password"] = config.smtp_password
    _speichere_config(db, daten)
    return {"status": "gespeichert"}


@router.post("/imap")
def speichere_imap(config: ImapConfig, db: Session = Depends(get_db)):
    """IMAP-Config in DB speichern."""
    daten = {
        "imap_host": config.imap_host,
        "imap_port": config.imap_port,
        "imap_user": config.imap_user,
    }
    if config.imap_password and config.imap_password != "••••••••":
        daten["imap_password"] = config.imap_password
    _speichere_config(db, daten)
    return {"status": "gespeichert"}


class SmtpTestRequest(BaseModel):
    test_empfaenger: Optional[str] = None


@router.post("/smtp/test")
def teste_smtp(req: SmtpTestRequest, db: Session = Depends(get_db)):
    """SMTP-Verbindung mit gespeicherter Config testen (kein Passwort-Input nötig)."""
    from app.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
    defaults = {
        "smtp_host": SMTP_HOST,
        "smtp_port": str(SMTP_PORT),
        "smtp_user": SMTP_USER,
        "smtp_password": SMTP_PASSWORD,
        "smtp_from": SMTP_FROM,
    }
    db_config = _lese_config(db, SMTP_KEYS)
    cfg = {**defaults, **{k: v for k, v in db_config.items() if v}}

    if not cfg.get("smtp_password"):
        return {"ok": False, "schritte": ["FEHLER: Kein Passwort gespeichert — bitte zuerst in Einstellungen speichern."]}

    ergebnis = test_smtp_verbindung(
        host=cfg["smtp_host"],
        port=int(cfg["smtp_port"]),
        user=cfg["smtp_user"],
        password=cfg["smtp_password"],
        from_addr=cfg["smtp_from"],
        test_empfaenger=req.test_empfaenger or None,
    )
    return ergebnis


@router.get("/versand-log")
def lese_versand_log(
    page: int = 1,
    per_page: int = 25,
    sort: str = "gesendet_am",
    order: str = "desc",
    nur_geoeffnet: bool = False,
    db: Session = Depends(get_db),
):
    """Versand-Log mit Pagination und Sortierung für das Dashboard."""
    from app.models import VersandLog
    from sqlalchemy import asc, desc, nullslast

    SORTIERBAR = {
        "id": VersandLog.id,
        "firmenname": VersandLog.firmenname,
        "email": VersandLog.email,
        "stufe": VersandLog.stufe,
        "gesendet_am": VersandLog.gesendet_am,
        "geoeffnet_am": VersandLog.geoeffnet_am,
    }
    sort_col = SORTIERBAR.get(sort, VersandLog.gesendet_am)
    sort_expr = nullslast(desc(sort_col)) if order == "desc" else nullslast(asc(sort_col))

    query = db.query(VersandLog)
    if nur_geoeffnet:
        query = query.filter(VersandLog.geoeffnet_am.isnot(None))

    total = query.count()
    offset = (page - 1) * per_page
    logs = query.order_by(sort_expr).offset(offset).limit(per_page).all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
        "items": [
            {
                "id": l.id,
                "email": l.email,
                "firmenname": l.firmenname,
                "stufe": l.stufe,
                "gesendet_am": l.gesendet_am.isoformat() if l.gesendet_am else None,
                "geoeffnet_am": l.geoeffnet_am.isoformat() if l.geoeffnet_am else None,
            }
            for l in logs
        ],
    }
