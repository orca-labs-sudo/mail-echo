import re
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.imap_service import get_unseen_emails
from app.models import Posteingang, VersandLog, Bounce
from pydantic import BaseModel

router = APIRouter()

# Typische Absender und Betreffs von NDR-Bounce-Mails
_BOUNCE_ABSENDER = re.compile(
    r'(mailer-daemon|postmaster|mail\s*delivery|delivery\s*subsystem|undeliverable)',
    re.IGNORECASE
)
_BOUNCE_BETREFF = re.compile(
    r'(undelivered|delivery\s*status|mail\s*delivery\s*fail|bounce|nicht\s*zustellbar|zurück.*unzustellbar|failure\s*notice)',
    re.IGNORECASE
)
_EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')


def _ist_bounce(absender: str, betreff: str) -> bool:
    return bool(
        _BOUNCE_ABSENDER.search(absender or "") or
        _BOUNCE_BETREFF.search(betreff or "")
    )


def _extrahiere_bounce_email(plain_text: str, in_reply_to: str, db: Session) -> tuple:
    """Gibt (versand_id, email, firmenname, ansprechpartner) zurück."""
    # Priorität 1: In-Reply-To → direkter VersandLog-Treffer
    if in_reply_to:
        log = db.query(VersandLog).filter(VersandLog.smtp_message_id == in_reply_to).first()
        if log:
            return log.id, log.email, log.firmenname, log.ansprechpartner

    # Priorität 2: E-Mail-Adressen im Body gegen VersandLog abgleichen
    kandidaten = _EMAIL_RE.findall(plain_text or "")
    for kandidat in kandidaten:
        log = db.query(VersandLog).filter(VersandLog.email == kandidat).first()
        if log:
            return log.id, log.email, log.firmenname, log.ansprechpartner

    return None, None, None, None

class AuswertungRequest(BaseModel):
    entscheidung: str
    notiz: str

@router.post("/fetch")
def fetch_emails(db: Session = Depends(get_db)):
    emails = get_unseen_emails()
    neue_antworten = 0
    neue_bounces = 0
    nicht_zugeordnet = 0

    for em in emails:
        # Bounce-Mails separat behandeln
        if _ist_bounce(em["absender"], em["betreff"]):
            versand_id, email, firmenname, ansprechpartner = _extrahiere_bounce_email(
                em["plain_text"], em["in_reply_to"], db
            )
            # Doppelte Bounces verhindern (gleiche imap_uid)
            exist = db.query(Bounce).filter(Bounce.bounce_betreff == em["betreff"],
                                            Bounce.email == email).first() if email else None
            if not exist:
                db.add(Bounce(
                    versand_id=versand_id,
                    email=email,
                    firmenname=firmenname,
                    ansprechpartner=ansprechpartner,
                    bounce_betreff=em["betreff"],
                    bounce_nachricht=em["plain_text"][:2000] if em["plain_text"] else None,
                ))
                neue_bounces += 1
            continue

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
    return {"neue_antworten": neue_antworten, "neue_bounces": neue_bounces, "nicht_zugeordnet": nicht_zugeordnet}

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
