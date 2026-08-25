import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Virtual Binary MLM API"
    ENV: str = os.getenv("ENV", "development")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "virtual-binary-mlm-super-secret-key-2026")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Database URL - default to SQLite for instant local run, supports PostgreSQL
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./mlm_demo.db")

    # MLM Business Rules Configuration
    DEFAULT_PACKAGE_PRICE: float = 35000.0
    DEFAULT_PRODUCT_VALUE: float = 30000.0
    DEFAULT_GST_AMOUNT: float = 5000.0
    DEFAULT_PACKAGE_BV: float = 30000.0

    # Commissions
    DIRECT_REFERRAL_COMMISSION_PCT: float = 0.10   # 10% on BV (₹3,000 for 30k BV)
    BINARY_MATCHING_COMMISSION_PCT: float = 0.10   # 10% on matched BV
    CARRY_FORWARD_ENABLED: bool = True

    # Frontend URL for CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    class Config:
        case_sensitive = True

settings = Settings()
