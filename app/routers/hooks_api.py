"""
Interne API-Endpunkte für Claude — Abrufen und Bestätigen von Hook-Ereignissen.
Prefix: /api/hooks
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import UnterlagenAnfrage, InteresseKlick

router = APIRouter()


@router.get("/unterlagen/offen")
def get_offene_unterlagen(db: Session = Depends(get_db)):
    eintraege = db.query(UnterlagenAnfrage).filter(UnterlagenAnfrage.verarbeitet == False).all()
    return [
        {
            "id": a.id,
            "email": a.email,
            "firmenname": a.firmenname,
            "ansprechpartner": a.ansprechpartner,
            "stufe_2_gesendet": a.stufe_2_gesendet,
            "angeklickt_am": a.angeklickt_am.isoformat() if a.angeklickt_am else None,
        }
        for a in eintraege
    ]


@router.post("/unterlagen/{id}/bestaetigen")
def bestaetigen_unterlagen(id: int, db: Session = Depends(get_db)):
    a = db.query(UnterlagenAnfrage).filter(UnterlagenAnfrage.id == id).first()
    if not a:
        return {"status": "not found"}
    a.verarbeitet = True
    db.commit()
    return {"status": "ok"}


@router.get("/interesse/offen")
def get_offene_interesse(db: Session = Depends(get_db)):
    eintraege = db.query(InteresseKlick).filter(InteresseKlick.verarbeitet == False).all()
    return [
        {
            "id": k.id,
            "email": k.email,
            "firmenname": k.firmenname,
            "angeklickt_am": k.angeklickt_am.isoformat() if k.angeklickt_am else None,
        }
        for k in eintraege
    ]


@router.post("/interesse/{id}/bestaetigen")
def bestaetigen_interesse(id: int, db: Session = Depends(get_db)):
    k = db.query(InteresseKlick).filter(InteresseKlick.id == id).first()
    if not k:
        return {"status": "not found"}
    k.verarbeitet = True
    db.commit()
    return {"status": "ok"}
