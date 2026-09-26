from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, inspect

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import engine, Base
import app.models.user  # ensures models are loaded


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- AUTOMATIC DATABASE MIGRATION ON STARTUP ---
    try:
        # Create tables if they do not exist
        Base.metadata.create_all(bind=engine)

        # Automatically check and add missing OTP columns to 'users' table
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
                    conn.execute(
                        text("ALTER TABLE users ADD COLUMN reset_otp_expires_at TIMESTAMPTZ;")
                    )
                    conn.commit()

        print(">>> [DATABASE] Automatic schema verification complete.")
    except Exception as e:
        print(f">>> [DATABASE ERROR] Could not auto-migrate: {e}")

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