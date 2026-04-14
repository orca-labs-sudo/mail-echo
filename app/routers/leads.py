from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Lead
from pydantic import BaseModel
from typing import List, Optional
import csv
import io

router = APIRouter()

class LeadUpdate(BaseModel):
    status: str

@router.post("/import")
async def import_leads(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    string_io = io.StringIO(content.decode("utf-8", errors="ignore"))
    reader = csv.reader(string_io, delimiter=";")
    
    importiert = 0
    duplikate = 0
    fehler = 0
    fehlerliste = []
    
    header_skipped = False
    
    for row in reader:
        if not row:
            continue
        if not header_skipped and "email" in str(row).lower():
            header_skipped = True
            continue
            
        if len(row) < 2:
            fehler += 1
            fehlerliste.append({"row": row, "error": "Zu wenige Spalten"})
            continue
            
        firmenname = row[0].strip()
        email = row[1].strip()
        ansprechpartner = row[2].strip() if len(row) > 2 else ""
        telefon = row[3].strip() if len(row) > 3 else ""
        branche = row[4].strip() if len(row) > 4 else ""
        
        if not email:
            fehler += 1
            fehlerliste.append({"row": row, "error": "E-Mail fehlt"})
            continue
            
        exist = db.query(Lead).filter(Lead.email == email).first()
        if exist:
            duplikate += 1
            continue
            
        new_lead = Lead(
            firmenname=firmenname,
            email=email,
            ansprechpartner=ansprechpartner,
            telefon=telefon,
            branche=branche,
            status="neu"
        )
        db.add(new_lead)
        importiert += 1
        
    db.commit()
    
    return {
        "importiert": importiert,
        "duplikate": duplikate,
        "fehler": fehler,
        "fehlerliste": fehlerliste
    }

@router.get("/")
def get_leads(status: Optional[str] = None, stufe_faellig: Optional[int] = None, db: Session = Depends(get_db)):
    query = db.query(Lead)
    if status:
        query = query.filter(Lead.status == status)
    return query.all()

@router.get("/{id}")
def get_lead(id: int, db: Session = Depends(get_db)):
    return db.query(Lead).filter(Lead.id == id).first()

@router.patch("/{id}")
def update_lead(id: int, lead_update: LeadUpdate, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == id).first()
    if lead:
        lead.status = lead_update.status
        db.commit()
    return lead

@router.get("/abmeldungen/offen")
def get_offene_abmeldungen(db: Session = Depends(get_db)):
    leads = db.query(Lead).filter(
        Lead.status == "abgemeldet",
        Lead.abmeldung_verarbeitet == False
    ).all()
    return [
        {
            "lead_id": l.id,
            "firmenname": l.firmenname,
            "email": l.email,
            "ansprechpartner": l.ansprechpartner,
            "abgemeldet_am": l.abgemeldet_am.isoformat() if l.abgemeldet_am else None,
        }
        for l in leads
    ]

@router.post("/{id}/abmeldung-bestaetigen")
def abmeldung_bestaetigen(id: int, db: Session = Depends(get_db)):
    lead = db.query(Lead).filter(Lead.id == id).first()
    if not lead:
        return {"status": "not found"}
    lead.abmeldung_verarbeitet = True
    db.commit()
    return {"status": "ok", "lead_id": id}
