import imaplib
import email
from email.header import decode_header
import datetime
import logging

logger = logging.getLogger(__name__)


def get_imap_config() -> dict:
    """Liest IMAP-Config aus DB (Priorität) oder .env (Fallback)."""
    from app.config import IMAP_HOST, IMAP_PORT, IMAP_USER, IMAP_PASSWORD
    defaults = {
        "imap_host": IMAP_HOST,
        "imap_port": IMAP_PORT,
        "imap_user": IMAP_USER,
        "imap_password": IMAP_PASSWORD,
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
            merged["imap_port"] = int(merged["imap_port"])
            return merged
        finally:
            db.close()
    except Exception as e:
        logger.warning(f"DB-Config nicht lesbar, nutze .env: {e}")
        return defaults


def get_unseen_emails():
    """Fetches unseen emails from the INBOX and marks them as read."""
    cfg = get_imap_config()
    host = cfg["imap_host"]
    port = cfg["imap_port"]
    user = cfg["imap_user"]
    password = cfg["imap_password"]

    logger.info(f"IMAP-Verbindung zu {host}:{port} als {user}")

    mail = None
    try:
        mail = imaplib.IMAP4_SSL(host, port)
        mail.login(user, password)
        mail.select("inbox")

        status, messages = mail.search(None, "UNSEEN")

        if status != "OK" or not messages[0]:
            mail.close()
            mail.logout()
            return []

        mail_ids = messages[0].split()
        results = []

        for _id in mail_ids:
            try:
                res, msg_data = mail.fetch(_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])

                        # Subject dekodieren — None-safe
                        raw_subject = msg.get("Subject")
                        if raw_subject:
                            subject, encoding = decode_header(raw_subject)[0]
                            if isinstance(subject, bytes):
                                subject = subject.decode(encoding if encoding else "utf-8", errors="ignore")
                        else:
                            subject = "(kein Betreff)"

                        from_ = msg.get("From", "")
                        in_reply_to = msg.get("In-Reply-To", "")

                        # Payload extrahieren — NoneType-safe
                        plain_text = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    payload = part.get_payload(decode=True)
                                    if payload is not None:
                                        plain_text += payload.decode('utf-8', errors='ignore')
                        else:
                            if msg.get_content_type() == "text/plain":
                                payload = msg.get_payload(decode=True)
                                if payload is not None:
                                    plain_text = payload.decode('utf-8', errors='ignore')

                        message_id = msg.get("Message-ID", "")

                        results.append({
                            "imap_uid": message_id,
                            "absender": from_,
                            "betreff": subject,
                            "plain_text": plain_text.strip(),
                            "in_reply_to": in_reply_to,
                            "empfangen_am": datetime.datetime.now()
                        })
            except Exception as e:
                # Einzelne Mail fehlgeschlagen — weiter mit der nächsten
                logger.error(f"Fehler beim Verarbeiten von Mail {_id}: {e}", exc_info=True)
                continue

        mail.close()
        mail.logout()
        return results

    except imaplib.IMAP4.error as e:
        logger.error(f"IMAP-Authentifizierung/Protokollfehler: {e}", exc_info=True)
        raise ConnectionError(f"IMAP-Fehler: {e}")
    except (ConnectionRefusedError, TimeoutError, OSError) as e:
        logger.error(f"IMAP-Verbindung zu {host}:{port} fehlgeschlagen: {e}", exc_info=True)
        raise ConnectionError(f"IMAP-Verbindung fehlgeschlagen: {e}")
    except Exception as e:
        logger.error(f"Unerwarteter IMAP-Fehler: {e}", exc_info=True)
        raise ConnectionError(f"IMAP unerwarteter Fehler: {e}")
    finally:
        # Verbindung aufräumen falls noch offen
        if mail is not None:
            try:
                mail.logout()
            except Exception:
                pass
