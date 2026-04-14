from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.imap_service import get_unseen_emails
from app.models import Posteingang, VersandLog
from pydantic import BaseModel

router = APIRouter()

class AuswertungRequest(BaseModel):
    entscheidung: str
    notiz: str

@router.post("/fetch")
def fetch_emails(db: Session = Depends(get_db)):
    emails = get_unseen_emails()
    neue_antworten = 0
    nicht_zugeordnet = 0

    for em in emails:
        exist = db.query(Posteingang).filter(Posteingang.imap_uid == em["imap_uid"]).first()
        if exist:
            continue

        versand_id = None
        if em["in_reply_to"]:
            log = db.query(VersandLog).filter(VersandLog.smtp_message_id == em["in_reply_to"]).first()
            if log:
                versand_id = log.id

        if not versand_id:
            nicht_zugeordnet += 1

        pe = Posteingang(
            versand_id=versand_id,
            imap_uid=em["imap_uid"],
            absender=em["absender"],
            betreff=em["betreff"],
            plain_text=em["plain_text"],
            empfangen_am=em["empfangen_am"]
        )
        db.add(pe)
        neue_antworten += 1

    db.commit()
    return {"neue_antworten": neue_antworten, "nicht_zugeordnet": nicht_zugeordnet}

@router.get("/")
def get_posteingang(db: Session = Depends(get_db)):
    eintraege = db.query(Posteingang).filter(Posteingang.verarbeitet == False).all()
    result = []
    for pe in eintraege:
        eintrag = {
            "id": pe.id,
            "absender": pe.absender,
            "betreff": pe.betreff,
            "plain_text": pe.plain_text,
            "empfangen_am": pe.empfangen_am.isoformat() if pe.empfangen_am else None,
            "versand_id": pe.versand_id,
            "firmenname": None,
            "stufe": None,
        }
        if pe.versand_id:
            log = db.query(VersandLog).filter(VersandLog.id == pe.versand_id).first()
            if log:
                eintrag["firmenname"] = log.firmenname
                eintrag["stufe"] = log.stufe
        result.append(eintrag)
    return result

@router.post("/{id}/auswerten")
def auswerten(id: int, request: AuswertungRequest, db: Session = Depends(get_db)):
    pe = db.query(Posteingang).filter(Posteingang.id == id).first()
    if pe:
        pe.ki_entscheidung = request.entscheidung
        pe.ki_notiz = request.notiz
        pe.verarbeitet = True
        db.commit()
        return {"status": "success"}
    return {"status": "not found"}
