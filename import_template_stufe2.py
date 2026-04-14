"""
Einmaliges Import-Skript: AWR24 Stufe-2-Template in die DB eintragen.
Ausführen im Container: python import_template_stufe2.py
"""
import sys
import os
sys.path.insert(0, "/app")

from app.database import SessionLocal
from app.models import MailTemplate

HTML = """<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="color-scheme" content="light">
  <meta name="supported-color-schemes" content="light">
  <style>
    :root { color-scheme: light; }
  </style>
</head>
<body style="margin:0;padding:0;background:#f0f0f0;font-family:Arial,Helvetica,sans-serif;color:#333">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f0f0f0;padding:30px 0">
  <tr><td align="center">
  <table width="680" cellpadding="0" cellspacing="0" style="background:#fff;box-shadow:0 2px 12px rgba(0,0,0,0.12)">

    <!-- KOPF: Logo links, Kanzlei-Info rechts -->
    <tr>
      <td style="padding:28px 40px 20px 40px;background:#fff">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="width:45%;padding:0;vertical-align:middle;background:#fff">
              <a href="https://awr24.de" style="text-decoration:none;display:inline-block;background:#fff">
                <img src="https://techniker0.me/awr_logo.png" height="100" alt="AWR24"
                     style="display:block;height:100px;width:auto;background:#fff">
              </a>
            </td>
            <td style="width:55%;padding:0;vertical-align:top;text-align:right">
              <div style="font-size:14px;font-weight:700;color:#222;letter-spacing:0.5px">AWR24-Team</div>
              <div style="font-size:11px;color:#555;margin-bottom:6px">Schadensregulierung</div>
              <div style="font-size:10px;color:#555;line-height:1.7">
                Mainblick 37<br>
                61476 Kronberg<br>
                Telefon: 06173 - 78 29 555<br>
                info@awr24.de<br>
                <a href="https://awr24.de" style="color:#555;text-decoration:none">awr24.de</a>
              </div>
            </td>
          </tr>
        </table>
      </td>
    </tr>

    <!-- TRENNLINIE -->
    <tr><td><hr style="border:none;border-top:1px solid #ddd;margin:0 40px"></td></tr>

    <!-- FREITEXT -->
    <tr>
      <td style="padding:28px 40px 36px 40px;font-size:13px;line-height:1.8;color:#222">

        <p style="margin:0 0 6px 0">Guten Tag, Team [FIRMA],</p>
        <p style="margin:0 0 6px 0">&nbsp;</p>

        <p style="margin:0 0 6px 0">vielen Dank für Ihr Interesse &mdash; hier sind Ihre Unterlagen.</p>
        <p style="margin:0 0 6px 0">&nbsp;</p>

        <p style="margin:0 0 6px 0"><strong>Vollmacht:</strong><br>
        Mit der ausgefüllten Vollmacht können wir sofort für Sie tätig werden. Einfach ausdrucken, unterschreiben und per WhatsApp oder E-Mail zurücksenden &mdash; den Rest erledigen wir.</p>
        <p style="margin:0 0 6px 0">&nbsp;</p>

        <!-- Button: Vollmacht -->
        <table cellpadding="0" cellspacing="0" style="margin-bottom:24px">
          <tr>
            <td style="background:#1a3a5c;border-radius:4px">
              <a href="https://awr24.de/wp-content/uploads/2025/06/Vollmacht-AWR.pdf"
                 style="display:inline-block;padding:12px 24px;font-size:13px;font-weight:700;color:#fff;text-decoration:none;letter-spacing:0.3px">
                &rarr; Vollmacht herunterladen (PDF)
              </a>
            </td>
          </tr>
        </table>

        <p style="margin:0 0 6px 0"><strong>Verhaltens-Tipps beim Unfall:</strong><br>
        Wie viele Fahrzeuge hat Ihr Fuhrpark? Schreiben Sie uns kurz &mdash; wir senden Ihnen für jedes Handschuhfach einen kompakten Spickzettel: Was tun, wen anrufen, was auf keinen Fall unterschreiben. Wenn Sie eine persönliche oder telefonische Beratung wünschen, schreiben Sie uns einfach &mdash; wir melden uns bei Ihnen.</p>
        <p style="margin:0 0 6px 0">&nbsp;</p>

        <p style="margin:0 0 6px 0"><strong>Gutachter &amp; Werkstatt:</strong><br>
        Falls Sie im Schadensfall einen unabhängigen Gutachter oder eine zuverlässige Werkstatt benötigen &mdash; wir haben bewährte Partner und empfehlen gerne weiter.</p>
        <p style="margin:0 0 6px 0">&nbsp;</p>

        <p style="margin:0 0 6px 0">Bei Fragen einfach melden &mdash; per WhatsApp, Telegram oder E-Mail. Wir sind für Sie da.</p>
        <p style="margin:0 0 6px 0">&nbsp;</p>

        <!-- Abmelden -->
        <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:8px">
          <tr>
            <td style="padding-top:8px">
              <a href="https://mail-echo.techniker0.me/hook/abmelden?uuid=[TRACKING_UUID]"
                 style="font-size:11px;color:#aaa;text-decoration:underline">
                Abmelden &mdash; keine weiteren Nachrichten
              </a>
            </td>
          </tr>
        </table>

      </td>
    </tr>

    <!-- FUSSZEILE -->
    <tr>
      <td style="background:#f8f8f8;padding:16px 40px 12px 40px;border-top:2px solid #ddd">

        <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:12px">
          <tr>
            <td style="font-size:10px;color:#555;line-height:1.7">
              <strong>Bankverbindung:</strong> Commerzbank AG &nbsp;|&nbsp;
              IBAN: DE78 5004 0000 0364 9142 00 &nbsp;|&nbsp;
              BIC: COBADEFFXXX &nbsp;|&nbsp; Steuer-Nr.: 013 882 01822
            </td>
          </tr>
        </table>

        <hr style="border:none;border-top:1px solid #ccc;margin:0 0 10px 0">

        <p style="margin:0 0 8px 0;font-size:9px;color:#999;line-height:1.5">
          <strong style="color:#777">VERTRAULICHKEITSHINWEIS:</strong>
          Der Inhalt dieser E-Mail ist vertraulich und ausschließlich für den Nutzer der E-Mail-Adresse bestimmt,
          an die die Nachricht geschickt wurde. Darüber hinaus kann sie durch besondere Bestimmungen geschützt sein.
          Wenn Sie nicht der Adressat dieser E-Mail sind, dürfen Sie diese nicht kopieren, weiterleiten, weitergeben
          oder sie ganz oder teilweise in irgendeiner Weise nutzen. Wenn Sie diese E-Mail fälschlicherweise erhalten
          haben, bitte benachrichtigen Sie den Absender, indem Sie auf diese Nachricht antworten.
        </p>

        <p style="margin:0;font-size:10px;color:#bbb">
          AWR24 &middot;
          <a href="mailto:info@awr24.de" style="color:#bbb">info@awr24.de</a> &middot;
          <a href="https://awr24.de" style="color:#999;font-weight:600">awr24.de</a>
        </p>

      </td>
    </tr>

  </table>
  </td></tr>
</table>
</body>
</html>"""

def main():
    db = SessionLocal()
    try:
        # Prüfen ob bereits vorhanden
        existing = db.query(MailTemplate).filter(
            MailTemplate.stufe == 2,
            MailTemplate.name == "AWR24 Unterlagen-Mail"
        ).first()

        if existing:
            print(f"Template bereits vorhanden (ID {existing.id}). Aktualisiere...")
            existing.betreff = "Ihre Unterlagen — AWR24 Schadensregulierung"
            existing.html_body = HTML
            db.commit()
            print(f"Template ID {existing.id} aktualisiert.")
        else:
            tpl = MailTemplate(
                name="AWR24 Unterlagen-Mail",
                stufe=2,
                betreff="Ihre Unterlagen — AWR24 Schadensregulierung",
                html_body=HTML,
                freigegeben=False,
            )
            db.add(tpl)
            db.commit()
            db.refresh(tpl)
            print(f"Template importiert: ID {tpl.id}, Stufe {tpl.stufe}")
            print("Bitte im Dashboard prüfen und freigeben!")
    finally:
        db.close()

if __name__ == "__main__":
    main()
