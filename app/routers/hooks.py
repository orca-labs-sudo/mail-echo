"""
Öffentliche Hook-Endpunkte — werden direkt von Links in Mails aufgerufen.
Prefix: /hook
"""
from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import asyncio

from app.database import get_db, SessionLocal
from app.models import VersandLog, Abmeldung, HookKlick

router = APIRouter()

HOMEPAGE_REDIRECT = "https://awr24.de"
PREVIEW_UUID = "preview-uuid"
SCANNER_WARTE_SEKUNDEN = 5.5
SCANNER_FENSTER_SEKUNDEN = 10
SCANNER_MIN_EVENTS = 2


async def _pruefe_scanner(uuid: str, hook_typ: str):
    """
    Wartet kurz, dann prüft: kamen ≥2 Events für dieselbe UUID in kurzer Zeit?
    Wenn ja → Scanner, alle Events als scanner=True markieren.
    Echter Klick bleibt unverändert in hook_klicks (verarbeitet=False, scanner=False)
    und ist damit für Claude über lese_unterlagen_anfragen() / lese_interesse_klicks() sichtbar.
    """
    await asyncio.sleep(SCANNER_WARTE_SEKUNDEN)

    db = SessionLocal()
    try:
        fenster_start = datetime.utcnow() - timedelta(seconds=SCANNER_FENSTER_SEKUNDEN)
        events = db.query(HookKlick).filter(
            HookKlick.tracking_uuid == uuid,
            HookKlick.hook_typ == hook_typ,
            HookKlick.geklickt_am >= fenster_start,
        ).all()

        if len(events) >= SCANNER_MIN_EVENTS:
            for e in events:
                e.scanner = True
            db.commit()
    finally:
        db.close()


@router.get("/unterlagen")
def hook_unterlagen(uuid: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if uuid == PREVIEW_UUID:
        return RedirectResponse(url=HOMEPAGE_REDIRECT)

    log = db.query(VersandLog).filter(VersandLog.tracking_uuid == uuid).first()
    if not log:
        return RedirectResponse(url=HOMEPAGE_REDIRECT)

    db.add(HookKlick(
        tracking_uuid=uuid,
        hook_typ="unterlagen",
        email=log.email,
        firmenname=log.firmenname,
        ansprechpartner=log.ansprechpartner,
    ))
    db.commit()

    background_tasks.add_task(_pruefe_scanner, uuid, "unterlagen")

    return RedirectResponse(url=HOMEPAGE_REDIRECT)


@router.get("/interesse")
def hook_interesse(uuid: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if uuid == PREVIEW_UUID:
        return RedirectResponse(url=HOMEPAGE_REDIRECT)

    log = db.query(VersandLog).filter(VersandLog.tracking_uuid == uuid).first()
    if not log:
        return RedirectResponse(url=HOMEPAGE_REDIRECT)

    db.add(HookKlick(
        tracking_uuid=uuid,
        hook_typ="interesse",
        email=log.email,
        firmenname=log.firmenname,
        ansprechpartner=log.ansprechpartner,
    ))
    db.commit()

    background_tasks.add_task(_pruefe_scanner, uuid, "interesse")

    return RedirectResponse(url=HOMEPAGE_REDIRECT)


@router.get("/abmelden")
def hook_abmelden(uuid: str, db: Session = Depends(get_db)):
    log = db.query(VersandLog).filter(VersandLog.tracking_uuid == uuid).first()

    if log:
        hook_exists = db.query(HookKlick).filter(
            HookKlick.tracking_uuid == uuid, HookKlick.hook_typ == "abmelden"
        ).first()
        if not hook_exists:
            db.add(HookKlick(
                tracking_uuid=uuid,
                hook_typ="abmelden",
                email=log.email,
                firmenname=log.firmenname,
                ansprechpartner=log.ansprechpartner,
            ))

        exists = db.query(Abmeldung).filter(Abmeldung.email == log.email).first()
        if not exists:
            db.add(Abmeldung(email=log.email))
        db.commit()

    return HTMLResponse("""
    <html><body>
    <h2>Abmeldung erfolgreich</h2>
    <p>Sie wurden erfolgreich abgemeldet und erhalten keine weiteren E-Mails von uns.</p>
    </body></html>
    """)
