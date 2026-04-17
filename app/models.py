from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class MailTemplate(Base):
    __tablename__ = "mail_templates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    stufe = Column(Integer, nullable=False)
    betreff = Column(String, nullable=False)
    html_body = Column(String, nullable=False)
    freigegeben = Column(Boolean, default=False)
    erstellt_am = Column(DateTime, default=func.now())
    geaendert_am = Column(DateTime)

class VersandLog(Base):
    __tablename__ = "versand_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, nullable=False, index=True)
    firmenname = Column(String)
    ansprechpartner = Column(String)
    template_id = Column(Integer, ForeignKey("mail_templates.id"))
    stufe = Column(Integer)
    tracking_uuid = Column(String, unique=True, nullable=False)
    smtp_message_id = Column(String)
    gesendet_am = Column(DateTime, default=func.now())
    geoeffnet_am = Column(DateTime)

class Posteingang(Base):
    __tablename__ = "posteingang"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    versand_id = Column(Integer, ForeignKey("versand_log.id"), nullable=True)
    imap_uid = Column(String, unique=True, nullable=False)
    absender = Column(String)
    betreff = Column(String)
    plain_text = Column(String)
    empfangen_am = Column(DateTime)
    verarbeitet = Column(Boolean, default=False)
    ki_entscheidung = Column(String)
    ki_notiz = Column(String)

class Abmeldung(Base):
    __tablename__ = "abmeldungen"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False, index=True)
    abgemeldet_am = Column(DateTime, default=func.now())
    verarbeitet = Column(Boolean, default=False)

class UnterlagenAnfrage(Base):
    __tablename__ = "unterlagen_anfragen"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, nullable=False)
    firmenname = Column(String)
    ansprechpartner = Column(String)
    tracking_uuid = Column(String, nullable=False)
    stufe_2_gesendet = Column(Boolean, default=False)
    angeklickt_am = Column(DateTime, default=func.now())
    verarbeitet = Column(Boolean, default=False)

class InteresseKlick(Base):
    __tablename__ = "interesse_klicks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, nullable=False)
    firmenname = Column(String)
    tracking_uuid = Column(String, nullable=False)
    angeklickt_am = Column(DateTime, default=func.now())
    verarbeitet = Column(Boolean, default=False)


class HookKlick(Base):
    """Zentrale Tabelle für alle Hook-Klicks aus Mails (unterlagen / interesse / abmelden)."""
    __tablename__ = "hook_klicks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tracking_uuid = Column(String, nullable=False, index=True)
    hook_typ = Column(String, nullable=False)  # unterlagen | interesse | abmelden
    email = Column(String, nullable=False)
    firmenname = Column(String)
    ansprechpartner = Column(String)
    geklickt_am = Column(DateTime, default=func.now())
    verarbeitet = Column(Boolean, default=False)
    scanner = Column(Boolean, default=False)


class KonfigurationEintrag(Base):
    __tablename__ = "konfiguration"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    schluessel = Column(String, unique=True, nullable=False, index=True)
    wert = Column(String, nullable=True)
    geaendert_am = Column(DateTime, default=func.now(), onupdate=func.now())


class Bounce(Base):
    __tablename__ = "bounces"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    versand_id = Column(Integer, ForeignKey("versand_log.id"), nullable=True)
    email = Column(String, nullable=True, index=True)
    firmenname = Column(String, nullable=True)
    ansprechpartner = Column(String, nullable=True)
    bounce_betreff = Column(String)
    bounce_nachricht = Column(String)
    empfangen_am = Column(DateTime, default=func.now())
    verarbeitet = Column(Boolean, default=False)
