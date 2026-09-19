import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

DEV_FALLBACK_SECRET_KEYS = {
    "partner-network-rewards-super-secret-key-2026",
    "partner-network-rewards-dev-secret-key-change-in-production",
    "mlm-super-secret-key-change-in-production",
    "secret",
    "changeme",
    "default-secret-key"
}

class Settings(BaseSettings):
    APP_NAME: str = "Partner Network Rewards API"
    ENV: str = os.getenv("ENV", "development")
    APP_ENV: str = os.getenv("APP_ENV", os.getenv("ENV", "development"))
    SECRET_KEY: str = os.getenv("SECRET_KEY", "partner-network-rewards-super-secret-key-2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # SQLite Persistent Storage Configuration
    # Local Default: ./data/mlm.sqlite3
    # Production Default (Render Persistent Disk): /var/data/mlm.sqlite3
    SQLITE_DB_PATH: str = os.getenv(
        "SQLITE_DB_PATH",
        os.getenv("DATABASE_URL", "").replace("sqlite:///", "") if os.getenv("DATABASE_URL", "").startswith("sqlite:///") else "./data/mlm.sqlite3"
    )

    # Database URL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{os.path.abspath(os.getenv('SQLITE_DB_PATH', './data/mlm.sqlite3'))}"
    )

    # Backups directory
    BACKUP_DIR: str = os.getenv(
        "BACKUP_DIR",
        os.path.join(os.path.dirname(os.path.abspath(os.getenv("SQLITE_DB_PATH", "./data/mlm.sqlite3"))), "backups")
    )

    # MLM Business Rules Configuration
    DEFAULT_PACKAGE_PRICE: float = 35400.0
    DEFAULT_PRODUCT_VALUE: float = 30000.0
    DEFAULT_GST_AMOUNT: float = 5400.0
    DEFAULT_PACKAGE_BV: float = 30000.0

    # Commissions & Rates
    DIRECT_COMMISSION_RATE: float = 0.10           # 10% on BV (₹3,000 for 30k BV)
    DIRECT_REFERRAL_COMMISSION_PCT: float = 0.10   # Backward-compatible alias
    BINARY_MATCHING_COMMISSION_PCT: float = 0.0    # Upline/Matching commission disabled per client rule
    CARRY_FORWARD_ENABLED: bool = True
    EARNING_CAP_LIMIT: float = 300000.0            # ₹3,00,000 max eligible Direct + Pairing income per cycle

    # Matching Pair Bonus Engine Configuration
    PAIR_VOLUME: float = 30000.0                   # Qualifying BV threshold per leg (₹30,000)
    PAIR_QUALIFYING_BV: float = 30000.0            # Backward-compatible alias
    PAIR_BONUS: float = 10000.0                    # Pair Bonus amount per completed pair (₹10,000)
    PAIR_BONUS_AMOUNT: float = 10000.0             # Backward-compatible alias
    MAX_PAIRS_PER_SLOT: int = 1                    # Maximum paid pairs per calculation period/slot (1)
    MAX_PAIRS_PER_PERIOD: int = 1                  # Backward-compatible alias

    # Carry Commission (Override) Configuration - DISABLED per client final rule
    CARRY_COMMISSION_ENABLED: bool = False         # Upline carry/override commission disabled
    CARRY_COMMISSION_RATE: float = 0.0             # 0% rate
    CARRY_COMMISSION_BASE: str = "PAIR_BONUS"      # "PAIR_BONUS", "MATCHED_BV", "PAIR_VOLUME"

    # Matching / Upline Commission Configuration - DISABLED per client final rule
    MATCHING_COMMISSION_ENABLED: bool = False      # Matching commission disabled
    MATCHING_COMMISSION_RATE: float = 0.0          # 0% rate
    MATCHING_COMMISSION_BASE: str = "PAIR_BONUS"   # "PAIR_BONUS", "MATCHED_BV", "PAIR_VOLUME"

    TIMEZONE: str = "Asia/Kolkata"

    # Frontend URL & CORS Origins
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://web.mystatusads333.com")
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "")
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "")
    SOCKET_CORS_ORIGINS: str = os.getenv("SOCKET_CORS_ORIGINS", "")

    # Initial Production Administrator Provisioning
    INITIAL_ADMIN_BOOTSTRAP: bool = os.getenv("INITIAL_ADMIN_BOOTSTRAP", "false").lower() in ("true", "1", "yes")
    INITIAL_ADMIN_EMAIL: str = os.getenv("INITIAL_ADMIN_EMAIL", "")
    INITIAL_ADMIN_PASSWORD: str = os.getenv("INITIAL_ADMIN_PASSWORD", "")
    INITIAL_ADMIN_MOBILE: str = os.getenv("INITIAL_ADMIN_MOBILE", "9876500001")
    INITIAL_ADMIN_NAME: str = os.getenv("INITIAL_ADMIN_NAME", "System Admin")

    # Company Payment & UPI Configuration
    COMPANY_UPI_ID: str = os.getenv("COMPANY_UPI_ID", "mystatusads@icici")
    COMPANY_UPI_NAME: str = os.getenv("COMPANY_UPI_NAME", "MyStatus Platform")

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() in ("production", "prod") or self.ENV.lower() in ("production", "prod")

    @property
    def is_postgres(self) -> bool:
        db_u = self.DATABASE_URL.lower()
        return db_u.startswith("postgresql") or db_u.startswith("postgres")

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.lower().startswith("sqlite")

    @property
    def normalized_database_url(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url

    @property
    def sanitized_db_path(self) -> str:
        if self.is_sqlite:
            raw_path = self.DATABASE_URL.replace("sqlite:///", "")
            return Path(raw_path).as_posix()
        elif self.is_postgres:
            # Mask user credentials in logs/UI
            try:
                from sqlalchemy.engine.url import make_url
                u = make_url(self.DATABASE_URL)
                masked_netloc = f"***:***@{u.host}:{u.port or 5432}" if u.host else "postgresql-host"
                return f"postgresql://{masked_netloc}/{u.database or ''}"
            except Exception:
                return "postgresql-rds"
        return "non-sqlite"

    def validate_production_configuration(self):
        if self.is_production:
            if not self.is_postgres:
                raise RuntimeError(
                    "CRITICAL: Production environment requires a PostgreSQL DATABASE_URL. "
                    "SQLite fallback is strictly prohibited in production."
                )
            if not self.SECRET_KEY or not self.SECRET_KEY.strip() or self.SECRET_KEY in DEV_FALLBACK_SECRET_KEYS or len(self.SECRET_KEY) < 32:
                raise RuntimeError(
                    "CRITICAL: Production environment requires a strong, unique SECRET_KEY (minimum 32 characters) "
                    "supplied through the environment. Default/empty development fallback keys are strictly prohibited in production."
                )

    class Config:
        case_sensitive = True

settings = Settings()
settings.validate_production_configuration()

# Ensure SQLite database directory & backup directory exist when running with SQLite
if settings.is_sqlite:
    db_file = settings.DATABASE_URL.replace("sqlite:///", "")
    db_dir = os.path.dirname(os.path.abspath(db_file))
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
if settings.BACKUP_DIR:
    os.makedirs(os.path.abspath(settings.BACKUP_DIR), exist_ok=True)
