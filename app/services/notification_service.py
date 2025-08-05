from flask import current_app
from flask_mail import Message
from app.extensions import mail

def send_email(subject, recipients, html_body):
    """Send a generic email."""
    try:
        msg = Message(subject, sender=current_app.config['MAIL_USERNAME'], recipients=recipients)
        msg.html = html_body
        mail.send(msg)
    except Exception as e:
        current_app.logger.error(f"Email sending failed: {str(e)}")
