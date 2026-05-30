from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, pipelines, audits, users
from app.config import settings

app = FastAPI(title="Arclat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(pipelines.router)
app.include_router(audits.router)
app.include_router(users.router)

@app.get("/")
def health_check():
    return {"status": "ok"}
