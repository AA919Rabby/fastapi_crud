import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

def send_otp_email(recipient_email: str, otp_code: str):
    print("\n" + "=" * 50)
    print(f" [OTP CODE GENERATED]: {otp_code} for {recipient_email}")
    print("=" * 50 + "\n")

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Verification Code</h2>
            <p>Your one-time verification code is:</p>
            <h1 style="color: #2b6cb0; letter-spacing: 5px;">{otp_code}</h1>
            <p>This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.</p>
            <p style="color: #718096; font-size: 12px;">If you did not request this, please ignore this email.</p>
        </body>
    </html>
    """

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("[EMAIL NOTICE] SMTP credentials missing in .env. Email skipped.")
        return

    msg = MIMEMultipart()
    msg["From"] = f"{settings.PROJECT_NAME} <{settings.EMAILS_FROM_EMAIL or settings.SMTP_USER}>"
    msg["To"] = recipient_email
    msg["Subject"] = f"{settings.PROJECT_NAME} - Verification Code"
    msg.attach(MIMEText(html_content, "html"))

    # Attempt 1: Port 465 (SSL)
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=10) as server:
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(msg["From"], [recipient_email], msg.as_string())
        print(f">>> [SUCCESS] Email sent via Gmail Port 465 to {recipient_email}")
        return
    except Exception as e:
        print(f">>> [PORT 465 FAILED]: {e}")

    # Attempt 2: Port 587 (TLS Fallback)
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=10) as server:
            server.starttls(context=context)
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(msg["From"], [recipient_email], msg.as_string())
        print(f">>> [SUCCESS] Email sent via Gmail Port 587 to {recipient_email}")
        return
    except Exception as e:
        print(f">>> [PORT 587 FAILED]: {e}")