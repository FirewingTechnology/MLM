from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, SessionLocal, apply_migrations
from app.services.seed_service import initialize_production_baseline
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
    time,
    activation,
    security_pins
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Additive table creation & schema migrations
    Base.metadata.create_all(bind=engine)
    apply_migrations(engine)
    
    # 2. Safe baseline initialization (never deletes or overwrites existing records)
    db = SessionLocal()
    try:
        initialize_production_baseline(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Binary MLM Enterprise API",
    description="Production Binary MLM Enterprise Engine with persistent SQLite database, atomic volume propagation, and security PIN activation.",
    version="3.0.0",
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
app.include_router(activation.router)
app.include_router(security_pins.router)


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "framework": "FastAPI",
        "version": "3.0.0",
        "database": "sqlite_persistent",
        "environment": settings.APP_ENV,
        "mode": "DEMO MODE - NO REAL MONEY"
    }
