from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Bounce

router = APIRouter()


@router.get("/")
def lese_bounces(db: Session = Depends(get_db)):
    """Gibt alle unverarbeiteten Bounces zurück."""
    eintraege = db.query(Bounce).filter(Bounce.verarbeitet == False).all()
    return [
        {
            "id": b.id,
            "email": b.email,
            "firmenname": b.firmenname,
            "ansprechpartner": b.ansprechpartner,
            "bounce_betreff": b.bounce_betreff,
            "empfangen_am": b.empfangen_am.isoformat() if b.empfangen_am else None,
        }
        for b in eintraege
    ]


@router.post("/{bounce_id}/bestaetigen")
def bounce_bestaetigen(bounce_id: int, db: Session = Depends(get_db)):
    """Markiert einen Bounce als in PROD verarbeitet."""
    b = db.query(Bounce).filter(Bounce.id == bounce_id).first()
    if not b:
        return {"status": "not found"}
    b.verarbeitet = True
    db.commit()
    return {"status": "ok"}
