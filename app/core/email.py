import httpx
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

def send_otp_email(recipient_email: str, otp_code: str):
    print("\n" + "=" * 50)
    print(f" >>> [LIVE OTP GENERATED]: {otp_code} for {recipient_email}")
    print("=" * 50 + "\n")

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Password Recovery Code</h2>
            <p>Your one-time verification code is:</p>
            <h1 style="color: #2b6cb0; letter-spacing: 5px;">{otp_code}</h1>
            <p>This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.</p>
            <p style="color: #718096; font-size: 12px;">If you did not request this, please ignore this email.</p>
        </body>
    </html>
    """

    # 1. PRIORITY: HTTPS API via Resend (Port 443 - NEVER BLOCKED ON RENDER)
    if getattr(settings, 'RESEND_API_KEY', None) and settings.RESEND_API_KEY:
        try:
            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "from": f"{settings.PROJECT_NAME} <onboarding@resend.dev>",
                "to": recipient_email,
                "subject": f"{settings.PROJECT_NAME} - Verification Code",
                "html": html_content
            }
            with httpx.Client(timeout=8.0) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code in [200, 201]:
                    print(f">>> [SUCCESS] Email delivered via HTTPS to {recipient_email}")
                    return
                else:
                    print(f">>> [HTTP EMAIL NOTICE]: {res.text}")
        except Exception as e:
            print(f">>> [HTTP EMAIL EXCEPTION]: {e}")

    # 2. FALLBACK: Direct Gmail SMTP with short timeout (Works locally)
    if settings.SMTP_USER and settings.SMTP_PASSWORD:
        msg = MIMEMultipart()
        msg["From"] = f"{settings.PROJECT_NAME} <{settings.EMAILS_FROM_EMAIL or settings.SMTP_USER}>"
        msg["To"] = recipient_email
        msg["Subject"] = f"{settings.PROJECT_NAME} - Verification Code"
        msg.attach(MIMEText(html_content, "html"))

        # Port 465 with 5-second timeout so it never hangs your server
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=5.0) as server:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(msg["From"], [recipient_email], msg.as_string())
            print(f">>> [SUCCESS] Email delivered via Port 465 to {recipient_email}")
            return
        except Exception as e:
            print(f">>> [SMTP Port 465 blocked on cloud]: {e}")

        # Port 587 fallback with 5-second timeout
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP("smtp.gmail.com", 587, timeout=5.0) as server:
                server.starttls(context=context)
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(msg["From"], [recipient_email], msg.as_string())
            print(f">>> [SUCCESS] Email delivered via Port 587 to {recipient_email}")
            return
        except Exception as e:
            print(f">>> [SMTP Port 587 blocked on cloud]: {e}")