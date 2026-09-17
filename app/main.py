from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.core.config import settings

app=FastAPI(title=settings.PROJECT_NAME,version="1.0")

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

app.include_router(api_router,prefix="/api/v1")

@app.get("/health",tags=["health"])
def health_check():
    return {"message":"Healthy"}