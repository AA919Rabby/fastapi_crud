from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, inspect

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
import app.models.user
import app.models.service
import app.models.extensions  # Auto-load extensions tables
from app.core.seeder import seed_default_services


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create all tables automatically
    try:
        Base.metadata.create_all(bind=engine)
        print(">>> [DATABASE] All tables verified/created successfully.")
    except Exception as e:
        print(f">>> [DATABASE ERROR] Table creation failed: {e}")

    # 2. Check & add OTP columns to users table automatically
    try:
        with engine.connect() as conn:
            inspector = inspect(engine)
            if "users" in inspector.get_table_names():
                columns = [col["name"] for col in inspector.get_columns("users")]

                if "reset_otp" not in columns:
                    print(">>> [AUTO-MIGRATE] Adding 'reset_otp' column...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN reset_otp VARCHAR;"))
                    conn.commit()

                if "reset_otp_expires_at" not in columns:
                    print(">>> [AUTO-MIGRATE] Adding 'reset_otp_expires_at' column...")
                    conn.execute(text("ALTER TABLE users ADD COLUMN reset_otp_expires_at TIMESTAMPTZ;"))
                    conn.commit()
    except Exception as e:
        print(f">>> [DATABASE ERROR] Could not verify user columns: {e}")

    # 3. Seed services
    db = SessionLocal()
    try:
        seed_default_services(db)
    except Exception as e:
        print(f">>> [SEEDER ERROR] Failed to seed services: {e}")
        db.rollback()
    finally:
        db.close()

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0",
    lifespan=lifespan
)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://yourproductiondomain.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health_check():
    return {"message": "Healthy"}