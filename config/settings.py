"""
Configuration settings for the Phishing URL Detection API
"""

import os
from pathlib import Path
from typing import List, Optional

class Settings:
    """Application settings"""
    
    # API Configuration
    API_TITLE: str = "Phishing URL Detection API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "A machine learning-powered API for detecting phishing URLs"
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    WORKERS: int = int(os.getenv("WORKERS", 4))
    
    # Security Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALLOWED_HOSTS: List[str] = os.getenv("ALLOWED_HOSTS", "*").split(",")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    DEFAULT_RATE_LIMIT: str = os.getenv("DEFAULT_RATE_LIMIT", "100/minute")
    CHECK_URL_RATE_LIMIT: str = os.getenv("CHECK_URL_RATE_LIMIT", "60/minute")
    BATCH_CHECK_RATE_LIMIT: str = os.getenv("BATCH_CHECK_RATE_LIMIT", "10/minute")
    FEATURE_EXTRACTION_RATE_LIMIT: str = os.getenv("FEATURE_EXTRACTION_RATE_LIMIT", "30/minute")
    
    # Model Configuration
    DEFAULT_MODEL_TYPE: str = os.getenv("DEFAULT_MODEL_TYPE", "xgboost")
    MODEL_PATH: str = os.getenv("MODEL_PATH", "models/phishing_detector.joblib")
    AUTO_LOAD_MODEL: bool = os.getenv("AUTO_LOAD_MODEL", "true").lower() == "true"
    
    # Data Configuration
    MAX_URL_LENGTH: int = int(os.getenv("MAX_URL_LENGTH", 2000))
    MAX_BATCH_SIZE: int = int(os.getenv("MAX_BATCH_SIZE", 100))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = os.getenv("LOG_FILE", "logs/api.log")
    
    # Database Configuration (if needed in the future)
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    
    # Monitoring Configuration
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "false").lower() == "true"
    METRICS_PORT: int = int(os.getenv("METRICS_PORT", 9090))
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    CORS_ALLOW_CREDENTIALS: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
    CORS_ALLOW_METHODS: List[str] = os.getenv("CORS_ALLOW_METHODS", "*").split(",")
    CORS_ALLOW_HEADERS: List[str] = os.getenv("CORS_ALLOW_HEADERS", "*").split(",")
    
    # Feature Engineering Configuration
    FEATURE_EXTRACTION_TIMEOUT: int = int(os.getenv("FEATURE_EXTRACTION_TIMEOUT", 10))
    
    # Model Training Configuration
    TRAINING_DATA_PATH: str = os.getenv("TRAINING_DATA_PATH", "data/phishing_dataset.csv")
    PROCESSED_DATA_PATH: str = os.getenv("PROCESSED_DATA_PATH", "data/processed_features.csv")
    
    # Performance Configuration
    PREDICTION_CACHE_SIZE: int = int(os.getenv("PREDICTION_CACHE_SIZE", 1000))
    PREDICTION_CACHE_TTL: int = int(os.getenv("PREDICTION_CACHE_TTL", 3600))  # 1 hour
    
    @property
    def model_dir(self) -> Path:
        """Get model directory path"""
        return Path(self.MODEL_PATH).parent
    
    @property
    def data_dir(self) -> Path:
        """Get data directory path"""
        return Path(self.TRAINING_DATA_PATH).parent
    
    @property
    def log_dir(self) -> Path:
        """Get log directory path"""
        if self.LOG_FILE:
            return Path(self.LOG_FILE).parent
        return Path("logs")
    
    def create_directories(self):
        """Create necessary directories if they don't exist"""
        self.model_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)

# Global settings instance
settings = Settings()

# Environment-specific configurations
class DevelopmentSettings(Settings):
    """Development environment settings"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    RATE_LIMIT_ENABLED: bool = False

class ProductionSettings(Settings):
    """Production environment settings"""
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    RATE_LIMIT_ENABLED: bool = True
    CORS_ORIGINS: List[str] = ["https://yourdomain.com"]  # Specify actual domains
    
    # Enhanced security for production
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")  # Must be set in production
    ALLOWED_HOSTS: List[str] = os.getenv("ALLOWED_HOSTS", "").split(",")
    
    def __post_init__(self):
        if not self.SECRET_KEY:
            raise ValueError("SECRET_KEY must be set in production environment")
        if not self.ALLOWED_HOSTS or self.ALLOWED_HOSTS == [""]:
            raise ValueError("ALLOWED_HOSTS must be set in production environment")

class TestingSettings(Settings):
    """Testing environment settings"""
    DEBUG: bool = True
    LOG_LEVEL: str = "ERROR"
    RATE_LIMIT_ENABLED: bool = False
    MODEL_PATH: str = "tests/fixtures/test_model.joblib"
    TRAINING_DATA_PATH: str = "tests/fixtures/test_data.csv"

def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()

# For backward compatibility
settings = get_settings()
