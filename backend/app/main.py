from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.config import settings, Settings
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
    security_pins,
    rank_rewards,
    earning_cap,
    daily_rewards
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

def get_cors_origins(cfg: Settings = settings) -> list:
    """Computes allowed CORS origins based on environment and configuration.
    
    Reads from:
    1. ALLOWED_ORIGINS (comma-separated, e.g. from AWS Elastic Beanstalk)
    2. CORS_ORIGINS (comma-separated extra origins)
    3. SOCKET_CORS_ORIGINS (comma-separated origins)
    4. FRONTEND_URL (single frontend URL)
    5. Production defaults: http://web.mystatusads333.com, https://web.mystatusads333.com
    6. Development defaults: http://localhost:5173, http://127.0.0.1:5173, http://localhost:3000, http://127.0.0.1:3000
    """
    raw_sources = [
        cfg.ALLOWED_ORIGINS,
        cfg.CORS_ORIGINS,
        cfg.SOCKET_CORS_ORIGINS,
        cfg.FRONTEND_URL,
    ]
    
    origins = []
    for src in raw_sources:
        if src:
            for item in src.split(","):
                cleaned = item.strip().rstrip("/")
                # Avoid '*' in explicit origins when credentials are true
                if cleaned and cleaned != "*":
                    origins.append(cleaned)

    # Standard production and Render domains
    origins.extend([
        "https://mlm-frontend-id60.onrender.com",
        "http://web.mystatusads333.com",
        "https://web.mystatusads333.com",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ])

    # Deduplicate while preserving insertion order
    return list(dict.fromkeys(filter(None, origins)))

# Authoritative HTTP CORS configuration
allowed_origins = get_cors_origins(settings)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.onrender\.com",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,
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
app.include_router(rank_rewards.router)
app.include_router(earning_cap.router)
app.include_router(daily_rewards.router)


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
