from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from pydantic import BaseModel
from app.services.sequenz_service import berechne_faellige_leads
from app.services.template_service import render_template
from app.services.smtp_service import send_email
from app.models import Lead, MailTemplate, VersandLog
import uuid
import datetime

router = APIRouter()

class BatchRequest(BaseModel):
    stufe: int
    limit: int

@router.get("/tagesplanung")
def tagesplanung(db: Session = Depends(get_db)):
    return berechne_faellige_leads(db)

@router.post("/batch")
def process_batch(request: BatchRequest, db: Session = Depends(get_db)):
    if request.limit > 100:
        raise HTTPException(status_code=400, detail="Limit darf nicht größer als 100 sein")
        
    template = db.query(MailTemplate).filter(
        MailTemplate.stufe == request.stufe,
        MailTemplate.freigegeben == True
    ).first()
    
    if not template:
        raise HTTPException(status_code=400, detail=f"Kein freigegebenes Template für Stufe {request.stufe} gefunden")
        
    heute = datetime.datetime.now()
    tag_6 = heute - datetime.timedelta(days=6)
    tag_7 = heute - datetime.timedelta(days=7)
    blocked_status = ['geantwortet', 'abgemeldet', 'inaktiv', 'interessiert', 'kontakt_erbeten', 'ablehnung', 'abwesenheit']
    from sqlalchemy import not_
    
    if request.stufe == 1:
        leads = db.query(Lead).filter(Lead.status == "neu").limit(request.limit).all()
    elif request.stufe == 2:
        leads = db.query(Lead).filter(Lead.status == "mail_1_gesendet", Lead.mail_1_gesendet_am < tag_6, not_(Lead.status.in_(blocked_status))).limit(request.limit).all()
    elif request.stufe == 3:
        leads = db.query(Lead).filter(Lead.status == "mail_2_gesendet", Lead.mail_2_gesendet_am < tag_7, not_(Lead.status.in_(blocked_status))).limit(request.limit).all()
    else:
        raise HTTPException(status_code=400, detail="Ungültige Stufe")
        
    gesendet = 0
    fehler = 0
    fehlgeschlagen = []
    
    for lead in leads:
        tracking_uuid = str(uuid.uuid4())
        html_content = render_template(template, lead, tracking_uuid)
        
        try:
            msg_id = send_email(lead.email, template.betreff, html_content)
            
            log = VersandLog(
                lead_id=lead.id,
                template_id=template.id,
                stufe=request.stufe,
                tracking_uuid=tracking_uuid,
                smtp_message_id=msg_id
            )
            db.add(log)
            
            lead.status = f"mail_{request.stufe}_gesendet"
            if request.stufe == 1:
                lead.mail_1_gesendet_am = datetime.datetime.now()
            elif request.stufe == 2:
                lead.mail_2_gesendet_am = datetime.datetime.now()
            elif request.stufe == 3:
                lead.mail_3_gesendet_am = datetime.datetime.now()
                
            gesendet += 1
            
        except Exception as e:
            fehler += 1
            fehlgeschlagen.append({"lead_id": lead.id, "error": str(e)})
            
    db.commit()
    
    return {
        "gesendet": gesendet,
        "fehler": fehler,
        "fehlgeschlagen": fehlgeschlagen
    }
