"""
Öffentliche Hook-Endpunkte — werden direkt von Links in Mails aufgerufen.
Prefix: /hook
"""
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import VersandLog, Abmeldung, UnterlagenAnfrage, InteresseKlick, MailTemplate, HookKlick
from app.services.template_service import render_template
from app.services.smtp_service import send_email
import uuid as uuid_lib

router = APIRouter()

HOMEPAGE_REDIRECT = "https://awr24.de"
PREVIEW_UUID = "preview-uuid"


@router.get("/unterlagen")
def hook_unterlagen(uuid: str, db: Session = Depends(get_db)):
    # Preview-Modus: kein DB-Zugriff, direkt weiterleiten
    if uuid == PREVIEW_UUID:
        return RedirectResponse(url=HOMEPAGE_REDIRECT)

    log = db.query(VersandLog).filter(VersandLog.tracking_uuid == uuid).first()
    if not log:
        return RedirectResponse(url=HOMEPAGE_REDIRECT)

    # HookKlick zentral erfassen (einmalig)
    hook_exists = db.query(HookKlick).filter(
        HookKlick.tracking_uuid == uuid, HookKlick.hook_typ == "unterlagen"
    ).first()
    if not hook_exists:
        db.add(HookKlick(
            tracking_uuid=uuid,
            hook_typ="unterlagen",
            email=log.email,
            firmenname=log.firmenname,
            ansprechpartner=log.ansprechpartner,
        ))

    exists = db.query(UnterlagenAnfrage).filter(UnterlagenAnfrage.tracking_uuid == uuid).first()
    if not exists:
        anfrage = UnterlagenAnfrage(
            email=log.email,
            firmenname=log.firmenname,
            ansprechpartner=log.ansprechpartner,
            tracking_uuid=uuid,
        )
        db.add(anfrage)

        template = db.query(MailTemplate).filter(
            MailTemplate.stufe == 2,
            MailTemplate.freigegeben == True
        ).first()

        if template:
            # Kein Abmelde-Check: Lead hat aktiv auf den Unterlagen-Link geklickt
            # → aktive Zustimmung, Versand ist unabhängig vom Abmeldestatus erlaubt
            tracking_uuid_neu = str(uuid_lib.uuid4())
            html = render_template(template, log.email, log.firmenname or "", log.ansprechpartner or "", tracking_uuid_neu)
            try:
                msg_id = send_email(log.email, template.betreff, html)
                neuer_log = VersandLog(
                    email=log.email,
                    firmenname=log.firmenname,
                    ansprechpartner=log.ansprechpartner,
                    template_id=template.id,
                    stufe=2,
                    tracking_uuid=tracking_uuid_neu,
                    smtp_message_id=msg_id,
                )
                db.add(neuer_log)
                anfrage.stufe_2_gesendet = True
            except Exception:
                pass

        db.commit()

    return RedirectResponse(url=HOMEPAGE_REDIRECT)


@router.get("/interesse")
def hook_interesse(uuid: str, db: Session = Depends(get_db)):
    if uuid == PREVIEW_UUID:
        return RedirectResponse(url=HOMEPAGE_REDIRECT)

    log = db.query(VersandLog).filter(VersandLog.tracking_uuid == uuid).first()

    # HookKlick zentral erfassen
    hook_exists = db.query(HookKlick).filter(
        HookKlick.tracking_uuid == uuid, HookKlick.hook_typ == "interesse"
    ).first()
    if not hook_exists and log:
        db.add(HookKlick(
            tracking_uuid=uuid,
            hook_typ="interesse",
            email=log.email,
            firmenname=log.firmenname,
            ansprechpartner=log.ansprechpartner,
        ))

    exists = db.query(InteresseKlick).filter(InteresseKlick.tracking_uuid == uuid).first()
    if not exists and log:
        klick = InteresseKlick(email=log.email, firmenname=log.firmenname, tracking_uuid=uuid)
        db.add(klick)
    db.commit()

    return RedirectResponse(url=HOMEPAGE_REDIRECT)


@router.get("/abmelden")
def hook_abmelden(uuid: str, db: Session = Depends(get_db)):
    log = db.query(VersandLog).filter(VersandLog.tracking_uuid == uuid).first()

    if log:
        # HookKlick zentral erfassen
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
