from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
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
    # 1. Enforce strict configuration in production
    settings.validate_production_configuration()

    # 2. Additive table creation & schema migrations
    try:
        Base.metadata.create_all(bind=engine)
        apply_migrations(engine)
    except Exception as e:
        if settings.is_production:
            raise RuntimeError(f"CRITICAL: Failed to connect to production database or apply migrations: {e}")
        else:
            print(f"[Warning] Database initialization error: {e}")

    # 3. Safe baseline initialization (never deletes or overwrites existing records)
    db = SessionLocal()
    try:
        initialize_production_baseline(db)
    except Exception as e:
        if settings.is_production:
            raise RuntimeError(f"CRITICAL: Failed to initialize production baseline: {e}") from e
        else:
            print(f"[Warning] Baseline initialization error: {e}")
            raise
    finally:
        db.close()
    yield


app = FastAPI(
    title="Partner Network & Rewards API",
    description="Production Partner Network & Rewards Engine with AWS RDS PostgreSQL persistent database, atomic volume propagation, and security PIN activation.",
    version="3.0.0",
    lifespan=lifespan
)

# CORS configuration
allowed_origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]
if settings.CORS_ORIGINS:
    extra_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    allowed_origins.extend(extra_origins)

# Ensure unique and non-empty
allowed_origins = list(set(filter(None, allowed_origins)))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if "*" in allowed_origins or not settings.is_production else allowed_origins,
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
    db_connected = False
    db_error = None
    dialect_name = engine.dialect.name
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1;"))
            db_connected = True
    except Exception as e:
        db_connected = False
        db_error = str(e)

    payload = {
        "status": "healthy" if db_connected else "degraded",
        "framework": "FastAPI",
        "version": "3.0.0",
        "database": "connected" if db_connected else "disconnected",
        "dialect": dialect_name,
        "database_path": settings.sanitized_db_path,
        "environment": settings.APP_ENV
    }
    if not db_connected:
        payload["error"] = "Database connection failed"
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=payload)

    return payload
