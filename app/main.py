from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from sqlalchemy import text, inspect

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
import app.models.user
import app.models.service
import app.models.extensions
from app.core.seeder import seed_default_services

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create tables if not exist
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f">>> [DATABASE ERROR] {e}")

    # 2. Automatically add missing columns to 'users' table
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            if "users" in inspector.get_table_names():
                cols = [c["name"] for c in inspector.get_columns("users")]

                # Add first_name & last_name
                if "first_name" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN first_name VARCHAR;"))
                    conn.commit()
                if "last_name" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN last_name VARCHAR;"))
                    conn.commit()

                # Add OTP columns
                if "reset_otp" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN reset_otp VARCHAR;"))
                    conn.commit()
                if "reset_otp_expires_at" not in cols:
                    conn.execute(text("ALTER TABLE users ADD COLUMN reset_otp_expires_at TIMESTAMPTZ;"))
                    conn.commit()
    except Exception as e:
        print(f">>> [AUTO-MIGRATE NOTICE]: {e}")

    # 3. Seed services
    db = SessionLocal()
    try:
        seed_default_services(db)
    except Exception as e:
        print(f">>> [SEEDER NOTICE]: {e}")
        db.rollback()
    finally:
        db.close()

    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0",
    lifespan=lifespan
)

# Allow all origins, headers, and methods for Flutter Web (Chrome), iOS, and Android
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["health"])
def health_check():
    return {"message": "Healthy"}