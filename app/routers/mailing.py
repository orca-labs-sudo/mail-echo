from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from pydantic import BaseModel
from app.services.template_service import render_template
from app.services.smtp_service import send_email
from app.models import MailTemplate, VersandLog, Abmeldung
import uuid

router = APIRouter()

class SendeRequest(BaseModel):
    email: str
    ansprechpartner: str
    firmenname: str
    stufe: int
    bypass_abmeldung: bool = False

@router.post("/sende")
def sende_mail(request: SendeRequest, db: Session = Depends(get_db)):
    # Abgemeldet-Prüfung — wird übersprungen wenn Lead aktiv zugestimmt hat (z.B. Unterlagen-Klick)
    if not request.bypass_abmeldung:
        if db.query(Abmeldung).filter(Abmeldung.email == request.email).first():
            raise HTTPException(status_code=400, detail="E-Mail-Adresse ist abgemeldet")

    template = db.query(MailTemplate).filter(
        MailTemplate.stufe == request.stufe,
        MailTemplate.freigegeben == True
    ).first()

    if not template:
        raise HTTPException(status_code=400, detail=f"Kein freigegebenes Template für Stufe {request.stufe}")

    tracking_uuid = str(uuid.uuid4())
    html_content = render_template(template, request.email, request.firmenname, request.ansprechpartner, tracking_uuid)

    try:
        msg_id = send_email(request.email, template.betreff, html_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SMTP-Fehler: {str(e)}")

    log = VersandLog(
        email=request.email,
        firmenname=request.firmenname,
        ansprechpartner=request.ansprechpartner,
        template_id=template.id,
        stufe=request.stufe,
        tracking_uuid=tracking_uuid,
        smtp_message_id=msg_id
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    return {"status": "gesendet", "versand_id": log.id, "tracking_uuid": tracking_uuid}
