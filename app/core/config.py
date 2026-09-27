from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "MyServices"
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # SMTP Free Email Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = ""
    OTP_EXPIRE_MINUTES: int = 10

    RESEND_API_KEY: str = ""
    SSLCOMMERZ_STORE_ID: str = "testbox"
    SSLCOMMERZ_STORE_PASS: str = "qwerty"
    SSLCOMMERZ_IS_SANDBOX: bool = True
    BACKEND_BASE_URL: str = "http://127.0.0.1:8000"

    GEMINI_API_KEY: str = ""


    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()