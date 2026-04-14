from fastapi import APIRouter, Depends
from fastapi.responses import Response, HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import VersandLog, Abmeldung
import datetime

router = APIRouter()

PIXEL = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'

@router.get("/track/{uuid}/open.gif")
def track_open(uuid: str, db: Session = Depends(get_db)):
    log = db.query(VersandLog).filter(VersandLog.tracking_uuid == uuid).first()
    if log and not log.geoeffnet_am:
        log.geoeffnet_am = datetime.datetime.now()
        db.commit()
    return Response(content=PIXEL, media_type="image/gif")

@router.get("/unsubscribe/{tracking_uuid}")
def unsubscribe(tracking_uuid: str, db: Session = Depends(get_db)):
    log = db.query(VersandLog).filter(VersandLog.tracking_uuid == tracking_uuid).first()

    if log:
        exists = db.query(Abmeldung).filter(Abmeldung.email == log.email).first()
        if not exists:
            abmeldung = Abmeldung(email=log.email)
            db.add(abmeldung)
            db.commit()

    html = """
    <html><body>
    <h2>Abmeldung erfolgreich</h2>
    <p>Sie wurden erfolgreich abgemeldet und erhalten keine weiteren E-Mails von uns.</p>
    </body></html>
    """
    return HTMLResponse(content=html)
