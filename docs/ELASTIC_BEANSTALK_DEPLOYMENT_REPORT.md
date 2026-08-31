# AWS Elastic Beanstalk Production Deployment Report

**Application**: Partner Network & Rewards API (FastAPI + AWS RDS PostgreSQL)  
**Deployment Platform**: AWS Elastic Beanstalk (Python 3.11 on AL2023)  
**Package Path**: `deploy/mlm-backend-elastic-beanstalk.zip`  
**Test Suite Status**: **167 / 167 Passed** (100% pass rate, 0 regressions)  
**Status**: **100% DEPLOYMENT READY** (Zero MLM business logic alterations)

---

## 1. Core Deployment Specifications

| Specification | Configuration |
| :--- | :--- |
| **FastAPI Application Entrypoint** | **`app.main:app`** |
| **Production WSGI/ASGI Server** | **Gunicorn with Uvicorn Workers** (`UvicornWorker`) |
| **Procfile Command** | `web: gunicorn -k uvicorn.workers.UvicornWorker app.main:app --workers 4 --timeout 120 --bind 0.0.0.0:8000` |
| **Python Compatibility** | Python 3.10, 3.11, 3.12 (AWS EB Python 3.11 AL2023 recommended) |
| **Target Database Engine** | AWS RDS PostgreSQL (`postgresql+psycopg://` / `psycopg3`) |
| **Local Test Suite** | **167 / 167 Passed** (0 failures, 100% pass rate) |
| **Frontend Build** | **Passed** (0 errors) |

---

## 2. Environment Variables Configuration for Elastic Beanstalk

Set the following environment variables in the AWS Elastic Beanstalk Console (**Configuration -> Software -> Environment properties**):

```env
# Application Environment
APP_ENV=production
ENV=production

# Security Keys
SECRET_KEY=YOUR_SECURE_PRODUCTION_SECRET_KEY_HERE
JWT_SECRET_KEY=YOUR_SECURE_JWT_SECRET_KEY_HERE

# AWS RDS PostgreSQL Database URL (psycopg3 preferred)
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@mystatus-postgres.ap-south-1.rds.amazonaws.com:5432/DATABASE_NAME

# Initial Administrator Bootstrap (One-Time Only)
# Enable ONLY during first deployment if database is brand new:
INITIAL_ADMIN_BOOTSTRAP=false
INITIAL_ADMIN_EMAIL=admin@yourproductiondomain.com
INITIAL_ADMIN_PASSWORD=YourSecureProductionAdminPassword123!
INITIAL_ADMIN_MOBILE=9876500001
INITIAL_ADMIN_NAME=System Admin

# Frontend Domains & CORS
FRONTEND_URL=https://your-production-frontend.com
CORS_ORIGINS=https://your-production-frontend.com,https://admin.your-production-frontend.com

# Server Port (Elastic Beanstalk standard)
PORT=8000
```

> [!IMPORTANT]
> **Production Fail-Safe**: If `DATABASE_URL` is omitted or points to SQLite when `APP_ENV=production`, the application raises a `RuntimeError` immediately during startup and refuses to start, preventing silent SQLite fallbacks or split-brain states.

---

## 3. Hardened Administrator Provisioning Architecture

### Problem Solved
Previously, application startup reset the administrator password to `Admin@123` on every reboot. This behavior has been completely removed.

### New Production Bootstrap Rules:
1. **Existing Admin Password Immutability**:
   - If an administrator already exists in the database, application startup **NEVER** modifies its password, username, role, or active status.
2. **One-Time Provisioning via Environment Variables**:
   - When deploying to a brand-new empty database, set `INITIAL_ADMIN_BOOTSTRAP=true` with `INITIAL_ADMIN_EMAIL` and `INITIAL_ADMIN_PASSWORD` (minimum 8 characters).
   - Once the server boots and provisions the admin, set `INITIAL_ADMIN_BOOTSTRAP=false` (or remove the variables).
   - Even if `INITIAL_ADMIN_BOOTSTRAP=true` remains set, subsequent restarts are completely idempotent and will **never** alter or overwrite the existing administrator.
3. **Explicit CLI Bootstrap Utility**:
   - Operators can also bootstrap or manage the admin account via the dedicated CLI tool:
     ```bash
     python backend/scripts/bootstrap_admin.py \
       --email admin@yourproductiondomain.com \
       --password "YourSecurePassword123!"
     ```
4. **Administrative Password Change API**:
   - Authenticated administrators and users can securely update their password via:
     `POST /api/auth/change-password`
     Payload:
     ```json
     {
       "current_password": "CurrentPassword123!",
       "new_password": "NewSecurePassword456!",
       "confirm_new_password": "NewSecurePassword456!"
     }
     ```
   - Validates current password, enforces minimum 8 characters, and logs the change to the `audit_logs` table.

---

## 4. Deployment ZIP Structure & Integrity

```
mlm-backend-elastic-beanstalk.zip
├── Procfile                    <-- Root level
├── requirements.txt            <-- Root level
├── alembic.ini                 <-- Root level
├── Dockerfile                  <-- Root level
├── create_backup.py            <-- Root level
├── seed.py                     <-- Root level (Guarded with strict production block)
├── .ebignore                   <-- Root level
├── alembic/                    <-- All migration versions
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 67003a6bff01_add_ist_time_slot_system_and_demo_clock.py
│       ├── 9a8b7c6d5e4f_add_matching_commission_to_settlements.py
│       └── e8f9a0b1c2d3_postgresql_production_schema.py
├── app/                        <-- Core FastAPI application
│   ├── main.py                 <-- (Contains app instance: app.main:app)
│   ├── config.py
│   ├── database.py
│   ├── security.py
│   ├── models/                 <-- All 21 SQLAlchemy models
│   ├── routers/                <-- All API routers
│   ├── services/               <-- MLM calculations, wallet, PINs, settlements
│   └── middleware/
└── scripts/                    <-- Standalone migration & verification tools
    ├── bootstrap_admin.py
    ├── migrate_sqlite_to_postgres.py
    └── verify_rds_production.py
```

### Excluded Non-Production Artifacts:
- Local SQLite database files (`*.sqlite3`, `*.wal`, `*.shm`)
- Virtual environments (`venv/`, `.venv/`)
- Test files and test database fixtures (`tests/`)
- Cache directories (`.pytest_cache/`, `__pycache__/`, `*.pyc`)
- Local development backups (`data/backups/`)
- Local `.env` secrets

---

## 5. Production Safety Guarantees

1. **Non-Destructive Lifespan**:
   - `Base.metadata.create_all()` and `apply_migrations()` only perform non-destructive additive updates.
   - Startup **NEVER** drops tables, wipes users, or resets wallet balances.
2. **Strict Guard on `seed.py`**:
   - Explicitly guarded with `if settings.is_production: raise SystemExit` to prevent manual or automated execution in production.
3. **Database Health Verification (`/api/health`)**:
   - Executes `SELECT 1;` on PostgreSQL.
   - Returns HTTP 200 with `{ "status": "healthy", "database": "connected", "dialect": "postgresql" }` without exposing credentials.
   - Returns HTTP 503 if the database connection fails.
4. **Connection Pool & Concurrency**:
   - Configured with `pool_pre_ping=True`, `pool_size=10`, `max_overflow=20`, `pool_recycle=1800`.
   - Concurrency safety maintained via row-level locking (`with_for_update()`) on wallet transactions, PIN allocations, and slot settlements.
