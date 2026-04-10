from app.models import Lead, MailTemplate
from app.config import BASE_URL
from jinja2 import Template

HTML_WRAPPER = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: Arial, sans-serif; font-size: 14px; color: #333; line-height: 1.5;">
    {{ content|safe }}
    <img src="{{ pixel_url }}" width="1" height="1" alt="" style="display:none;" />
    <br><br>
    <div style="font-size: 11px; color: #999;">
        <a href="{{ unsub_url }}" style="color: #999;">Von zukünftigen Mails abmelden</a>
    </div>
</body>
</html>
"""

def render_template(template: MailTemplate, lead: Lead, tracking_uuid: str) -> str:
    text = template.html_body
    
    firma = lead.firmenname if lead.firmenname else "Unternehmen"
    ansprechpartner = lead.ansprechpartner if lead.ansprechpartner else "Damen und Herren"
    
    text = text.replace("[FIRMA]", firma)
    text = text.replace("[ANSPRECHPARTNER]", ansprechpartner)
    
    pixel_url = f"{BASE_URL}/track/{tracking_uuid}/open.gif"
    unsub_url = f"{BASE_URL}/unsubscribe/{lead.id}" 
    
    jinja_template = Template(HTML_WRAPPER)
    return jinja_template.render(
        content=text,
        pixel_url=pixel_url,
        unsub_url=unsub_url
    )

def render_preview(template: MailTemplate) -> str:
    class DummyLead:
        firmenname = "Mustermann GmbH"
        ansprechpartner = "Hr. Müller"
        id = 0
    return render_template(template, DummyLead(), "preview-uuid")
