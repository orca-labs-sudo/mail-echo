from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import leads, templates, mailing, tracking, posteingang, stats

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Mail-Echo Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://mail-echo.techniker0.me"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from fastapi import Depends
from app.database import get_db

app.mount("/static", StaticFiles(directory="ui/static"), name="static")
ui = Jinja2Templates(directory="ui/templates")

app.include_router(leads.router, prefix="/api/leads", tags=["leads"])
app.include_router(templates.router, prefix="/api/templates", tags=["templates"])
app.include_router(mailing.router, prefix="/api/mailing", tags=["mailing"])
app.include_router(tracking.router, tags=["tracking"])
app.include_router(posteingang.router, prefix="/api/posteingang", tags=["posteingang"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])

@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    return ui.TemplateResponse("base.html", {"request": request})

@app.get("/leads", response_class=HTMLResponse)
def view_leads(request: Request):
    return ui.TemplateResponse("leads.html", {"request": request})

@app.get("/templates", response_class=HTMLResponse)
def view_templates(request: Request):
    return ui.TemplateResponse("templates_list.html", {"request": request})

@app.get("/templates/new", response_class=HTMLResponse)
def new_template(request: Request):
    return ui.TemplateResponse("template_edit.html", {"request": request, "template": None})

@app.get("/templates/{id}/edit", response_class=HTMLResponse)
def edit_template(request: Request, id: int, db: Session = Depends(get_db)):
    from app.models import MailTemplate
    tpl = db.query(MailTemplate).filter(MailTemplate.id == id).first()
    return ui.TemplateResponse("template_edit.html", {"request": request, "template": tpl})

@app.get("/stats", response_class=HTMLResponse)
def view_stats(request: Request):
    return ui.TemplateResponse("stats.html", {"request": request})
