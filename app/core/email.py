import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

def send_otp_email(recipient_email: str, otp_code: str):
    # Always print OTP to the terminal for debugging
    print("\n" + "=" * 50)
    print(f" [OTP CODE]: {otp_code} for {recipient_email}")
    print("=" * 50 + "\n")

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("[EMAIL] SMTP credentials missing. Skipping email send.")
        return

    msg = MIMEMultipart()
    msg["From"] = settings.EMAILS_FROM_EMAIL or settings.SMTP_USER
    msg["To"] = recipient_email
    msg["Subject"] = f"{settings.PROJECT_NAME} - OTP Verification code"

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2>Password Recovery</h2>
            <p>Your one-time verification code is:</p>
            <h1 style="color: #2b6cb0; letter-spacing: 5px;">{otp_code}</h1>
            <p>This code will expire in {settings.OTP_EXPIRE_MINUTES} minutes.</p>
            <p style="color: #718096; font-size: 12px;">If you did not request this, please ignore this email.</p>
        </body>
    </html>
    """
    msg.attach(MIMEText(html_content, "html"))

    try:
        context = ssl.create_default_context()

        # If port 465, use direct SSL (Most reliable for Gmail)
        if int(settings.SMTP_PORT) == 465:
            with smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, context=context) as server:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(msg["From"], [recipient_email], msg.as_string())
        else:
            # Fallback for port 587
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.sendmail(msg["From"], [recipient_email], msg.as_string())

        print(f">>> [SUCCESS] Email successfully sent to {recipient_email}!")
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email: {e}")