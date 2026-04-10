from sqlalchemy.orm import Session
from sqlalchemy import not_
from app.models import Lead
import datetime

def berechne_faellige_leads(db: Session):
    heute = datetime.datetime.now()
    tag_6 = heute - datetime.timedelta(days=6)
    tag_7 = heute - datetime.timedelta(days=7)
    
    blocked_status = ['geantwortet', 'abgemeldet', 'inaktiv', 'interessiert', 'kontakt_erbeten', 'ablehnung', 'abwesenheit']
    
    # stufe 1 faellig
    stufe_1 = db.query(Lead).filter(Lead.status == "neu").count()
    
    # stufe 2 faellig
    stufe_2 = db.query(Lead).filter(
        Lead.status == "mail_1_gesendet",
        Lead.mail_1_gesendet_am < tag_6,
        not_(Lead.status.in_(blocked_status))
    ).count()
    
    # stufe 3 faellig
    stufe_3 = db.query(Lead).filter(
        Lead.status == "mail_2_gesendet",
        Lead.mail_2_gesendet_am < tag_7,
        not_(Lead.status.in_(blocked_status))
    ).count()
    
    return {
        "stufe_1": stufe_1,
        "stufe_2": stufe_2,
        "stufe_3": stufe_3
    }
