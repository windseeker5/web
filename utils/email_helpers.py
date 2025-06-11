# utils/email_helpers.py

from flask import render_template
from flask_mail import Message, Mail
import os

 
#from app import mail
from utils.mail import mail

mail = Mail()

def init_mail(app):
    app.config['MAIL_SERVER'] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config['MAIL_PORT'] = int(os.getenv("MAIL_PORT", 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv("MAIL_DEFAULT_SENDER", "info@minipass.me")
    mail.init_app(app)




def send_user_deployment_email(to, url, password):
    subject = "🎉 Your minipass app is live!"  # ✅ Lowercase "minipass"
    
    # ✅ Render with admin email included
    html = render_template(
        "emails/deployment_ready.html",
        url=url,
        password=password,
        user_email=to
    )

    msg = Message(
        subject,
        recipients=[to],
        html=html,
        body=f"Your app is live: {url}\nAdmin Email: {to}\nPassword: {password}"
    )

    # ✅ Attach welcome-icon.png as inline image (fixed header format)
    icon_path = os.path.join("static", "image", "welcome-icon.png")
    with open(icon_path, "rb") as f:
        msg.attach(
            filename="welcome-icon.png",
            content_type="image/png",
            data=f.read(),
            disposition="inline",
            headers={"Content-ID": "<welcome-icon.png>"}  # ✅ THIS LINE FIXED
        )

    mail.send(msg)






def send_support_error_email(user_email, app_name, error_log):
    subject = f"[MiniPass Deployment Error] {app_name}"
    tech_support = "kdresdell@gmail.com"
    recipients = [user_email]
    cc = [tech_support]

    html_body = f"""
    <p>Hi,</p>
    <p>We encountered an issue while deploying your MiniPass app: <strong>{app_name}</strong>.</p>
    <p>Our technical team has been notified and will investigate shortly. You will receive a follow-up email once the deployment is complete.</p>
    <hr>
    <pre style="background:#f8f9fa;padding:10px;border-radius:5px;font-size:0.9rem;">{error_log}</pre>
    <p>— MiniPass Deployment Bot</p>
    """

    msg = Message(subject=subject, recipients=recipients, cc=cc, html=html_body)
    mail.send(msg)

