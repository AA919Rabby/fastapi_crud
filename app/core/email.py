import httpx
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

def send_otp_email(recipient_email: str, otp_code: str):
    print("\n" + "=" * 50)
    print(f" [OTP CODE]: {otp_code} for {recipient_email}")
    print("=" * 50 + "\n")

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Your Verification Code</h2>
            <p>Your one-time recovery code is:</p>
            <h1 style="color: #2b6cb0; letter-spacing: 5px;">{otp_code}</h1>
            <p>This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.</p>
            <p style="color: #718096; font-size: 12px;">If you did not request this, please ignore this email.</p>
        </body>
    </html>
    """

    # 1. SMTP Attempt with Port 465 (SSL)
    if settings.SMTP_USER and settings.SMTP_PASSWORD:
        try:
            msg = MIMEMultipart()
            msg["From"] = f"{settings.PROJECT_NAME} <{settings.EMAILS_FROM_EMAIL or settings.SMTP_USER}>"
            msg["To"] = recipient_email
            msg["Subject"] = f"{settings.PROJECT_NAME} - Your Verification Code"
            msg.attach(MIMEText(html_content, "html"))

            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=8) as server:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(msg["From"], [recipient_email], msg.as_string())
            print(f">>> [SUCCESS] Email delivered to {recipient_email}")
            return
        except Exception as e:
            print(f">>> [SMTP Port 465 Error]: {e}")

        # 2. SMTP Fallback with Port 587 (TLS)
        try:
            msg = MIMEMultipart()
            msg["From"] = f"{settings.PROJECT_NAME} <{settings.EMAILS_FROM_EMAIL or settings.SMTP_USER}>"
            msg["To"] = recipient_email
            msg["Subject"] = f"{settings.PROJECT_NAME} - Your Verification Code"
            msg.attach(MIMEText(html_content, "html"))

            context = ssl.create_default_context()
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=8) as server:
                server.starttls(context=context)
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(msg["From"], [recipient_email], msg.as_string())
            print(f">>> [SUCCESS] Email delivered via Port 587 to {recipient_email}")
            return
        except Exception as e:
            print(f">>> [SMTP Port 587 Error]: {e}")