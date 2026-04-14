from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.database import engine, Base
from app.routers import templates, mailing, tracking, posteingang, stats, abmeldungen
from app.config import DASHBOARD_USER, DASHBOARD_PASSWORD
import secrets

Base.metadata.create_all(bind=engine)

# Migrationen: neue Spalten/Tabellen zu bestehender DB hinzufügen
with engine.connect() as conn:
    from sqlalchemy import text
    for stmt in [
        "ALTER TABLE versand_log ADD COLUMN email TEXT",
        "ALTER TABLE versand_log ADD COLUMN firmenname TEXT",
    ]:
        try:
            conn.execute(text(stmt))
            conn.commit()
        except Exception:
            pass  # Spalte existiert bereits

app = FastAPI(title="Mail-Echo Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://mail-echo.techniker0.me"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBasic()

def require_auth(credentials: HTTPBasicCredentials = Depends(security)):
    ok_user = secrets.compare_digest(credentials.username.encode(), DASHBOARD_USER.encode())
    ok_pass = secrets.compare_digest(credentials.password.encode(), DASHBOARD_PASSWORD.encode())
    if not (ok_user and ok_pass):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Ungültige Zugangsdaten",
            headers={"WWW-Authenticate": "Basic"},
        )

from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from app.database import get_db

app.mount("/static", StaticFiles(directory="ui/static"), name="static")
ui = Jinja2Templates(directory="ui/templates")

app.include_router(templates.router, prefix="/api/templates", tags=["templates"])
app.include_router(mailing.router, prefix="/api/mailing", tags=["mailing"])
app.include_router(tracking.router, tags=["tracking"])
app.include_router(posteingang.router, prefix="/api/posteingang", tags=["posteingang"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(abmeldungen.router, prefix="/api/abmeldungen", tags=["abmeldungen"])

@app.get("/", response_class=HTMLResponse)
def root(request: Request, _=Depends(require_auth)):
    return ui.TemplateResponse(request, "base.html")

@app.get("/templates", response_class=HTMLResponse)
def view_templates(request: Request, _=Depends(require_auth)):
    return ui.TemplateResponse(request, "templates_list.html")

@app.get("/templates/new", response_class=HTMLResponse)
def new_template(request: Request, _=Depends(require_auth)):
    return ui.TemplateResponse(request, "template_edit.html", {"template": None})

@app.get("/templates/{id}/edit", response_class=HTMLResponse)
def edit_template(request: Request, id: int, db: Session = Depends(get_db), _=Depends(require_auth)):
    from app.models import MailTemplate
    tpl = db.query(MailTemplate).filter(MailTemplate.id == id).first()
    return ui.TemplateResponse(request, "template_edit.html", {"template": tpl})

@app.get("/stats", response_class=HTMLResponse)
def view_stats(request: Request, _=Depends(require_auth)):
    return ui.TemplateResponse(request, "stats.html")
