from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, SessionLocal, apply_migrations
from app.services.seed_service import seed_database
from app.routers import (
    auth,
    dashboard,
    network,
    referral,
    packages,
    purchases,
    wallet,
    commissions,
    withdrawals,
    admin,
    time
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create tables & migrate schema
    Base.metadata.create_all(bind=engine)
    apply_migrations(engine)
    
    # 2. Auto-seed initial demo dataset
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Virtual Binary MLM Demo API",
    description="High-performance backend for Binary MLM simulation and client demonstrations (DEMO MODE - NO REAL MONEY).",
    version="2.0.0",
    lifespan=lifespan
)

# CORS configuration
origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(auth.router)
app.include_router(dashboard.router)
app.include_router(network.router)
app.include_router(referral.router)
app.include_router(packages.router)
app.include_router(purchases.router)
app.include_router(wallet.router)
app.include_router(commissions.router)
app.include_router(withdrawals.router)
app.include_router(admin.router)
app.include_router(time.router)


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "framework": "FastAPI",
        "version": "2.0.0",
        "mode": "DEMO MODE - NO REAL MONEY"
    }
