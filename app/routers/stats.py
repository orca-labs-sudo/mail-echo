from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import VersandLog, Posteingang, Abmeldung

router = APIRouter()

@router.get("/")
def get_stats(db: Session = Depends(get_db)):
    stufe_1 = db.query(VersandLog).filter(VersandLog.stufe == 1).count()
    stufe_2 = db.query(VersandLog).filter(VersandLog.stufe == 2).count()
    stufe_3 = db.query(VersandLog).filter(VersandLog.stufe == 3).count()
    geoeffnet = db.query(VersandLog).filter(VersandLog.geoeffnet_am.isnot(None)).count()
    abmeldungen = db.query(Abmeldung).count()
    antworten = db.query(Posteingang).count()

    return {
        "mails_versendet": {"stufe_1": stufe_1, "stufe_2": stufe_2, "stufe_3": stufe_3},
        "mails_geoeffnet": geoeffnet,
        "abmeldungen": abmeldungen,
        "antworten": antworten,
    }

@router.get("/offnungen")
def get_offnungen(db: Session = Depends(get_db)):
    logs = db.query(VersandLog).filter(VersandLog.geoeffnet_am.isnot(None)).all()
    return [
        {
            "email": log.email,
            "firmenname": log.firmenname,
            "stufe": log.stufe,
            "gesendet_am": log.gesendet_am.isoformat() if log.gesendet_am else None,
            "geoeffnet_am": log.geoeffnet_am.isoformat() if log.geoeffnet_am else None,
        }
        for log in logs
    ]
