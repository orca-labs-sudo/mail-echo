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
