import imaplib
import email
from email.header import decode_header
from app.config import IMAP_HOST, IMAP_PORT, IMAP_USER, IMAP_PASSWORD
import datetime

def get_unseen_emails():
    """Fetches unseen emails from the INBOX and marks them as read."""
    mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    mail.login(IMAP_USER, IMAP_PASSWORD)
    mail.select("inbox")
    
    status, messages = mail.search(None, "UNSEEN")
    
    if status != "OK" or not messages[0]:
        mail.close()
        mail.logout()
        return []
    
    mail_ids = messages[0].split()
    results = []
    
    for _id in mail_ids:
        res, msg_data = mail.fetch(_id, "(RFC822)")
        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding if encoding else "utf-8")
                
                from_ = msg.get("From", "")
                in_reply_to = msg.get("In-Reply-To", "")
                
                plain_text = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            plain_text += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                else:
                    if msg.get_content_type() == "text/plain":
                        plain_text = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                
                message_id = msg.get("Message-ID", "")
                
                results.append({
                    "imap_uid": message_id,
                    "absender": from_,
                    "betreff": subject,
                    "plain_text": plain_text.strip(),
                    "in_reply_to": in_reply_to,
                    "empfangen_am": datetime.datetime.now()
                })
        
    mail.close()
    mail.logout()
    return results
