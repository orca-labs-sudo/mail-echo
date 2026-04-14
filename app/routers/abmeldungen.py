from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Abmeldung

router = APIRouter()

@router.get("/offen")
def get_offene_abmeldungen(db: Session = Depends(get_db)):
    eintraege = db.query(Abmeldung).filter(Abmeldung.verarbeitet == False).all()
    return [
        {
            "id": a.id,
            "email": a.email,
            "abgemeldet_am": a.abgemeldet_am.isoformat() if a.abgemeldet_am else None,
        }
        for a in eintraege
    ]

@router.post("/{id}/bestaetigen")
def bestaetigen(id: int, db: Session = Depends(get_db)):
    a = db.query(Abmeldung).filter(Abmeldung.id == id).first()
    if not a:
        return {"status": "not found"}
    a.verarbeitet = True
    db.commit()
    return {"status": "ok", "id": id}
