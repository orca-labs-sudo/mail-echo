from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.imap_service import get_unseen_emails
from app.models import Posteingang, Lead, VersandLog
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
            
        log = None
        lead_id = None
        versand_id = None
        
        if em["in_reply_to"]:
            log = db.query(VersandLog).filter(VersandLog.smtp_message_id == em["in_reply_to"]).first()
            if log:
                lead_id = log.lead_id
                versand_id = log.id
                
        if not lead_id:
            nicht_zugeordnet += 1
            
        pe = Posteingang(
            lead_id=lead_id,
            versand_id=versand_id,
            imap_uid=em["imap_uid"],
            absender=em["absender"],
            betreff=em["betreff"],
            plain_text=em["plain_text"],
            empfangen_am=em["empfangen_am"]
        )
        db.add(pe)
        
        if lead_id:
            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if lead and lead.status not in ["abgemeldet", "inaktiv"]:
                lead.status = "geantwortet"
                
        neue_antworten += 1
        
    db.commit()
    
    return {
        "neue_antworten": neue_antworten,
        "nicht_zugeordnet": nicht_zugeordnet
    }

@router.get("/")
def get_posteingang(db: Session = Depends(get_db)):
    return db.query(Posteingang).filter(Posteingang.verarbeitet == False).all()

@router.post("/{id}/auswerten")
def auswerten(id: int, request: AuswertungRequest, db: Session = Depends(get_db)):
    pe = db.query(Posteingang).filter(Posteingang.id == id).first()
    if pe:
        pe.ki_entscheidung = request.entscheidung
        pe.ki_notiz = request.notiz
        pe.verarbeitet = True
        
        if pe.lead_id:
            lead = db.query(Lead).filter(Lead.id == pe.lead_id).first()
            if lead:
                lead.status = request.entscheidung
                
        db.commit()
        return {"status": "success"}
    return {"status": "not found"}
