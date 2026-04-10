import os
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.ionos.de")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "")

IMAP_HOST = os.getenv("IMAP_HOST", "imap.ionos.de")
IMAP_PORT = int(os.getenv("IMAP_PORT", 993))
IMAP_USER = os.getenv("IMAP_USER", "")
IMAP_PASSWORD = os.getenv("IMAP_PASSWORD", "")

BASE_URL = os.getenv("BASE_URL", "http://localhost:8010")
SECRET_KEY = os.getenv("SECRET_KEY", "devsecret")
MCP_PORT = int(os.getenv("MCP_PORT", 8002))
APP_PORT = int(os.getenv("APP_PORT", 8010))

DATABASE_PATH = os.getenv("DATABASE_PATH", "./mail_echo.db")
