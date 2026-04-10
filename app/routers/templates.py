from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import MailTemplate
from pydantic import BaseModel
from typing import List
from app.services.template_service import render_preview
import datetime

router = APIRouter()

class TemplateCreate(BaseModel):
    name: str
    stufe: int
    betreff: str
    html_body: str

class TemplateUpdate(TemplateCreate):
    pass

@router.get("/")
def list_templates(db: Session = Depends(get_db)):
    return db.query(MailTemplate).all()

@router.post("/")
def create_template(template: TemplateCreate, db: Session = Depends(get_db)):
    new_tpl = MailTemplate(**template.model_dump())
    db.add(new_tpl)
    db.commit()
    db.refresh(new_tpl)
    return new_tpl

@router.get("/{id}")
def get_template(id: int, db: Session = Depends(get_db)):
    tpl = db.query(MailTemplate).filter(MailTemplate.id == id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return tpl

@router.put("/{id}")
def update_template(id: int, template_update: TemplateUpdate, db: Session = Depends(get_db)):
    tpl = db.query(MailTemplate).filter(MailTemplate.id == id).first()
    if tpl:
        tpl.name = template_update.name
        tpl.stufe = template_update.stufe
        tpl.betreff = template_update.betreff
        tpl.html_body = template_update.html_body
        tpl.geaendert_am = datetime.datetime.now()
        db.commit()
        db.refresh(tpl)
    return tpl

@router.post("/{id}/freigeben")
def freigeben_template(id: int, db: Session = Depends(get_db)):
    tpl = db.query(MailTemplate).filter(MailTemplate.id == id).first()
    if tpl:
        tpl.freigegeben = True
        db.commit()
    return {"status": "freigegeben"}

@router.get("/{id}/vorschau")
def vorschau_template(id: int, db: Session = Depends(get_db)):
    from fastapi.responses import HTMLResponse
    tpl = db.query(MailTemplate).filter(MailTemplate.id == id).first()
    if not tpl:
        raise HTTPException(status_code=404, detail="Template not found")
    html = render_preview(tpl)
    return HTMLResponse(content=html)
