import httpx
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
            <h2>Verification code</h2>
            <p>Your one-time verification code is:</p>
            <h1 style="color: #2b6cb0; letter-spacing: 5px;">{otp_code}</h1>
            <p>This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.</p>
            <p style="color: #718096; font-size: 12px;">If you did not request this code, please ignore this email.</p>
        </body>
    </html>
    """

    # Custom Sender Name: "MyServices Support <onboarding@resend.dev>"
    sender_display_name = f"{settings.PROJECT_NAME} Support <abcrabbi033@gmail.com>"

    # 1. PRIMARY: Resend API (HTTP Port 443 - NEVER BLOCKED BY RENDER)
    if settings.RESEND_API_KEY:
        try:
            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "from": sender_display_name,
                "to": recipient_email,
                "subject": f"{settings.PROJECT_NAME} - OTP Code",
                "html": html_content
            }
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, headers=headers, json=payload)
                if resp.status_code in [200, 201]:
                    print(f">>> [SUCCESS] Email sent via Resend API to {recipient_email}")
                    return
                else:
                    print(f">>> [RESEND ERROR]: {resp.text}")
        except Exception as e:
            print(f">>> [RESEND FAILED]: {e}")

    # 2. FALLBACK: Gmail SMTP (Works on Localhost)
    if settings.SMTP_USER and settings.SMTP_PASSWORD:
        try:
            msg = MIMEMultipart()
            msg["From"] = f"{settings.PROJECT_NAME} <{settings.EMAILS_FROM_EMAIL or settings.SMTP_USER}>"
            msg["To"] = recipient_email
            msg["Subject"] = f"{settings.PROJECT_NAME} - OTP Code"
            msg.attach(MIMEText(html_content, "html"))

            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(settings.SMTP_HOST, 465, context=context) as server:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(msg["From"], [recipient_email], msg.as_string())
            print(f">>> [SUCCESS] Email sent via SMTP to {recipient_email}")
        except Exception as e:
            print(f">>> [SMTP BLOCKED/FAILED]: {e}")