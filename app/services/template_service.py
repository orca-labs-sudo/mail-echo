from app.models import MailTemplate
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

def render_template(template: MailTemplate, email: str, firmenname: str, ansprechpartner: str, tracking_uuid: str) -> str:
    text = template.html_body

    firma = firmenname if firmenname else "Unternehmen"
    ap = ansprechpartner if ansprechpartner else "Damen und Herren"

    text = text.replace("[FIRMA]", firma)
    text = text.replace("[ANSPRECHPARTNER]", ap)

    pixel_url = f"{BASE_URL}/track/{tracking_uuid}/open.gif"
    unsub_url = f"{BASE_URL}/hook/abmelden?uuid={tracking_uuid}"

    jinja_template = Template(HTML_WRAPPER)
    return jinja_template.render(
        content=text,
        pixel_url=pixel_url,
        unsub_url=unsub_url
    )

def render_preview(template: MailTemplate) -> str:
    return render_template(template, "vorschau@beispiel.de", "Mustermann GmbH", "Hr. Müller", "preview-uuid")
