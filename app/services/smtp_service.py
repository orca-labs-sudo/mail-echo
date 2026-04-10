import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM
import uuid

def send_email(to_email: str, subject: str, html_content: str, message_id: str = None) -> str:
    """Sends an HTML email and returns the generated Message-ID."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    
    if not message_id:
        message_id = f"<{uuid.uuid4()}@mail-echo>"
        
    msg["Message-ID"] = message_id
    
    part = MIMEText(html_content, "html")
    msg.attach(part)
    
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()
    server.login(SMTP_USER, SMTP_PASSWORD)
    server.sendmail(SMTP_FROM, to_email, msg.as_string())
    server.quit()
    
    return message_id
