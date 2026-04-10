from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Lead, VersandLog, Posteingang
from sqlalchemy import func

router = APIRouter()

@router.get("/")
def get_stats(db: Session = Depends(get_db)):
    total_leads = db.query(Lead).count()
    mail_1 = db.query(Lead).filter(Lead.mail_1_gesendet_am.isnot(None)).count()
    mail_2 = db.query(Lead).filter(Lead.mail_2_gesendet_am.isnot(None)).count()
    mail_3 = db.query(Lead).filter(Lead.mail_3_gesendet_am.isnot(None)).count()
    
    opened = db.query(VersandLog).filter(VersandLog.geoeffnet_am.isnot(None)).count()
    
    status_counts = db.query(Lead.status, func.count(Lead.id)).group_by(Lead.status).all()
    stats_dict = {s: c for s, c in status_counts}
    
    return {
        "gesamt_leads": total_leads,
        "mails_versendet": {
            "stufe_1": mail_1,
            "stufe_2": mail_2,
            "stufe_3": mail_3
        },
        "mails_geoeffnet": opened,
        "status_verteilung": stats_dict
    }
