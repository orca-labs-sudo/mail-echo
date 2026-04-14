"""
Interne API-Endpunkte für Claude — Abrufen und Bestätigen von Hook-Ereignissen.
Prefix: /api/hooks
Datenquelle: HookKlick-Tabelle (zentral für alle Klick-Typen).
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import HookKlick

router = APIRouter()


def _klicks_als_liste(eintraege: list) -> list:
    return [
        {
            "id": k.id,
            "tracking_uuid": k.tracking_uuid,
            "hook_typ": k.hook_typ,
            "email": k.email,
            "firmenname": k.firmenname,
            "ansprechpartner": k.ansprechpartner,
            "geklickt_am": k.geklickt_am.isoformat() if k.geklickt_am else None,
        }
        for k in eintraege
    ]


@router.get("/unterlagen/offen")
def get_offene_unterlagen(db: Session = Depends(get_db)):
    """Unterlagen-Anfragen die noch nicht in PROD verarbeitet wurden."""
    eintraege = db.query(HookKlick).filter(
        HookKlick.hook_typ == "unterlagen",
        HookKlick.verarbeitet == False,
    ).order_by(HookKlick.geklickt_am.desc()).all()
    return _klicks_als_liste(eintraege)


@router.post("/unterlagen/{id}/bestaetigen")
def bestaetigen_unterlagen(id: int, db: Session = Depends(get_db)):
    """Markiert eine Unterlagen-Anfrage als in PROD verarbeitet."""
    k = db.query(HookKlick).filter(HookKlick.id == id).first()
    if not k:
        return {"status": "not found"}
    k.verarbeitet = True
    db.commit()
    return {"status": "ok", "id": id}


@router.get("/interesse/offen")
def get_offene_interesse(db: Session = Depends(get_db)):
    """Interesse-Klicks die noch nicht in PROD verarbeitet wurden."""
    eintraege = db.query(HookKlick).filter(
        HookKlick.hook_typ == "interesse",
        HookKlick.verarbeitet == False,
    ).order_by(HookKlick.geklickt_am.desc()).all()
    return _klicks_als_liste(eintraege)


@router.post("/interesse/{id}/bestaetigen")
def bestaetigen_interesse(id: int, db: Session = Depends(get_db)):
    """Markiert einen Interesse-Klick als in PROD verarbeitet."""
    k = db.query(HookKlick).filter(HookKlick.id == id).first()
    if not k:
        return {"status": "not found"}
    k.verarbeitet = True
    db.commit()
    return {"status": "ok", "id": id}


@router.get("/abmelden/offen")
def get_offene_abmeldungen(db: Session = Depends(get_db)):
    """Abmeldungen die noch nicht in PROD nachgepflegt wurden."""
    eintraege = db.query(HookKlick).filter(
        HookKlick.hook_typ == "abmelden",
        HookKlick.verarbeitet == False,
    ).order_by(HookKlick.geklickt_am.desc()).all()
    return _klicks_als_liste(eintraege)


@router.post("/abmelden/{id}/bestaetigen")
def bestaetigen_abmeldung(id: int, db: Session = Depends(get_db)):
    """Markiert eine Abmeldung als in PROD nachgepflegt."""
    k = db.query(HookKlick).filter(HookKlick.id == id).first()
    if not k:
        return {"status": "not found"}
    k.verarbeitet = True
    db.commit()
    return {"status": "ok", "id": id}
