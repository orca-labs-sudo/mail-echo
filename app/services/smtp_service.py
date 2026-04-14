import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import uuid

logger = logging.getLogger(__name__)


def get_smtp_config() -> dict:
    """Liest SMTP-Config aus DB (Priorität) oder .env (Fallback)."""
    from app.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
    defaults = {
        "smtp_host": SMTP_HOST,
        "smtp_port": SMTP_PORT,
        "smtp_user": SMTP_USER,
        "smtp_password": SMTP_PASSWORD,
        "smtp_from": SMTP_FROM,
    }
    try:
        from app.database import SessionLocal
        from app.models import KonfigurationEintrag
        db = SessionLocal()
        try:
            keys = list(defaults.keys())
            eintraege = db.query(KonfigurationEintrag).filter(
                KonfigurationEintrag.schluessel.in_(keys)
            ).all()
            db_config = {e.schluessel: e.wert for e in eintraege if e.wert}
            merged = {**defaults, **db_config}
            merged["smtp_port"] = int(merged["smtp_port"])
            return merged
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"DB-Config nicht lesbar, nutze .env: {e}")
        return defaults


def send_email(to_email: str, subject: str, html_content: str, message_id: str = None) -> str:
    """Sendet eine HTML-Mail und gibt die Message-ID zurück."""
    cfg = get_smtp_config()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg["smtp_from"]
    msg["To"] = to_email

    if not message_id:
        message_id = f"<{uuid.uuid4()}@mail-echo>"

    msg["Message-ID"] = message_id

    part = MIMEText(html_content, "html")
    msg.attach(part)

    logger.info(f"SMTP-Verbindung zu {cfg['smtp_host']}:{cfg['smtp_port']} für {to_email}")
    try:
        server = smtplib.SMTP(cfg["smtp_host"], cfg["smtp_port"], timeout=15)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(cfg["smtp_user"], cfg["smtp_password"])
        server.sendmail(cfg["smtp_from"], to_email, msg.as_string())
        server.quit()
        logger.info(f"Mail erfolgreich gesendet an {to_email} (Message-ID: {message_id})")
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP-Authentifizierung fehlgeschlagen: {e}")
        raise
    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"Empfänger abgelehnt {to_email}: {e}")
        raise
    except smtplib.SMTPException as e:
        logger.error(f"SMTP-Fehler beim Senden an {to_email}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unbekannter Fehler beim Senden an {to_email}: {e}")
        raise

    return message_id


def test_smtp_verbindung(host: str, port: int, user: str, password: str, from_addr: str, test_empfaenger: str = None) -> dict:
    """Testet SMTP-Verbindung und sendet optional eine Test-Mail."""
    schritte = []
    try:
        schritte.append("Verbinde zu SMTP-Server...")
        server = smtplib.SMTP(host, port, timeout=10)
        schritte.append(f"Verbunden mit {host}:{port}")

        server.ehlo()
        schritte.append("EHLO OK")

        server.starttls()
        schritte.append("STARTTLS OK")

        server.ehlo()
        server.login(user, password)
        schritte.append(f"Anmeldung als {user} OK")

        if test_empfaenger:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = "Mail-Echo SMTP-Test"
            msg["From"] = from_addr
            msg["To"] = test_empfaenger
            msg["Message-ID"] = f"<test-{uuid.uuid4()}@mail-echo>"
            msg.attach(MIMEText("<p>SMTP-Verbindungstest von Mail-Echo war erfolgreich.</p>", "html"))
            server.sendmail(from_addr, test_empfaenger, msg.as_string())
            schritte.append(f"Test-Mail gesendet an {test_empfaenger}")

        server.quit()
        return {"ok": True, "schritte": schritte}

    except smtplib.SMTPAuthenticationError:
        schritte.append("FEHLER: Authentifizierung fehlgeschlagen — Benutzername oder Passwort falsch")
        return {"ok": False, "schritte": schritte}
    except smtplib.SMTPConnectError:
        schritte.append(f"FEHLER: Verbindung zu {host}:{port} nicht möglich")
        return {"ok": False, "schritte": schritte}
    except Exception as e:
        schritte.append(f"FEHLER: {str(e)}")
        return {"ok": False, "schritte": schritte}
