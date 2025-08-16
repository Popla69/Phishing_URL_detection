from fastapi import FastAPI, HTTPException, Depends, status, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any
import uvicorn
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
try:
    import validators
    VALIDATORS_AVAILABLE = True
except ImportError:
    VALIDATORS_AVAILABLE = False
    print("Warning: validators not available. Using basic URL validation.")
import time
import logging
from datetime import datetime
import asyncio
import os
from pathlib import Path

# Import our custom modules
from .preprocessing import URLFeatureExtractor
from .ml_model import PhishingDetectionModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title="Phishing URL Detection API",
    description="A machine learning-powered API for detecting phishing URLs",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for model and feature extractor
model: Optional[PhishingDetectionModel] = None
feature_extractor: Optional[URLFeatureExtractor] = None
model_stats = {
    "loaded": False,
    "model_type": None,
    "last_prediction_time": None,
    "total_predictions": 0,
    "phishing_detected": 0,
    "legitimate_detected": 0
}

# Security
security = HTTPBearer(auto_error=False)

# Pydantic models for request/response
class URLCheckRequest(BaseModel):
    url: str
    
    @validator('url')
    def validate_url(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('URL cannot be empty')
        
        url = v.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        # Use validators if available, otherwise basic validation
        if VALIDATORS_AVAILABLE:
            if not validators.url(url):
                raise ValueError('Invalid URL format')
        else:
            if not basic_url_validation(url):
                raise ValueError('Invalid URL format')
        
        if len(url) > 2000:  # Reasonable URL length limit
            raise ValueError('URL too long (max 2000 characters)')
        
        return url

class URLCheckResponse(BaseModel):
    url: str
    is_phishing: bool
    phishing_probability: float
    legitimate_probability: float
    confidence: float
    risk_level: str
    timestamp: datetime
    processing_time_ms: float

class BatchURLRequest(BaseModel):
    urls: List[str]
    
    @validator('urls')
    def validate_urls(cls, v):
        if not v:
            raise ValueError('URLs list cannot be empty')
        if len(v) > 100:  # Limit batch size
            raise ValueError('Maximum 100 URLs per batch request')
        
        validated_urls = []
        for url in v:
            if not url or len(url.strip()) == 0:
                continue
            
            url = url.strip()
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
            
            # Use validators if available, otherwise basic validation
            if VALIDATORS_AVAILABLE:
                is_valid = validators.url(url)
            else:
                is_valid = basic_url_validation(url)
            
            if is_valid and len(url) <= 2000:
                validated_urls.append(url)
        
        if not validated_urls:
            raise ValueError('No valid URLs found in the list')
        
        return validated_urls

class BatchURLResponse(BaseModel):
    results: List[URLCheckResponse]
    total_processed: int
    phishing_count: int
    legitimate_count: int
    processing_time_ms: float

class ModelStatusResponse(BaseModel):
    loaded: bool
    model_type: Optional[str]
    total_predictions: int
    phishing_detected: int
    legitimate_detected: int
    uptime_seconds: float
    last_prediction_time: Optional[datetime]

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    model_status: str
    api_version: str

# Startup event
@app.on_event("startup")
async def startup_event():
    """Load model and initialize components on startup"""
    global model, feature_extractor, model_stats
    
    logger.info("Starting up Phishing Detection API...")
    
    # Initialize feature extractor
    feature_extractor = URLFeatureExtractor()
    logger.info("Feature extractor initialized")
    
    # Try to load pre-trained model
    model_path = Path("models/phishing_detector.joblib")
    if model_path.exists():
        try:
            model = PhishingDetectionModel()
            model.load_model(str(model_path))
            model_stats["loaded"] = True
            model_stats["model_type"] = model.model_type
            logger.info(f"Loaded pre-trained {model.model_type} model")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            model = None
    else:
        logger.warning("No pre-trained model found. Model training required.")
        model = None
    
    logger.info("API startup complete")

# Helper functions for URL validation
def basic_url_validation(url: str) -> bool:
    """Basic URL validation when validators package is not available"""
    if not url:
        return False
    
    # Check if it starts with http/https
    if not url.startswith(('http://', 'https://')):
        return False
    
    # Basic pattern check
    import re
    pattern = r'^https?://[\w\.-]+\.[a-zA-Z]{2,}.*$'
    return bool(re.match(pattern, url))

# Authentication dependency (optional)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Optional authentication - can be extended with actual auth logic"""
    if credentials is None:
        return None
    # Add your authentication logic here
    return {"user": "anonymous"}

# Helper functions
def get_risk_level(probability: float) -> str:
    """Determine risk level based on phishing probability"""
    if probability >= 0.8:
        return "HIGH"
    elif probability >= 0.6:
        return "MEDIUM"
    elif probability >= 0.4:
        return "LOW"
    else:
        return "VERY_LOW"

def update_stats(is_phishing: bool):
    """Update global statistics"""
    global model_stats
    model_stats["total_predictions"] += 1
    model_stats["last_prediction_time"] = datetime.now()
    
    if is_phishing:
        model_stats["phishing_detected"] += 1
    else:
        model_stats["legitimate_detected"] += 1

# API Endpoints
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with basic API information"""
    return {
        "message": "Phishing URL Detection API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    model_status = "loaded" if model_stats["loaded"] else "not_loaded"
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        model_status=model_status,
        api_version="1.0.0"
    )

@app.get("/status", response_model=ModelStatusResponse)
@limiter.limit("30/minute")
async def model_status(request):
    """Get model status and statistics"""
    return ModelStatusResponse(
        loaded=model_stats["loaded"],
        model_type=model_stats.get("model_type"),
        total_predictions=model_stats["total_predictions"],
        phishing_detected=model_stats["phishing_detected"],
        legitimate_detected=model_stats["legitimate_detected"],
        uptime_seconds=(datetime.now() - datetime.now()).total_seconds(),  # Would be calculated from startup time
        last_prediction_time=model_stats["last_prediction_time"]
    )

@app.post("/check-url", response_model=URLCheckResponse)
@limiter.limit("60/minute")
async def check_url(request, url_request: URLCheckRequest, user=Depends(get_current_user)):
    """Check if a single URL is phishing or legitimate"""
    if not model_stats["loaded"] or model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded. Please train and load a model first."
        )
    
    start_time = time.time()
    
    try:
        # Extract features from URL
        features = feature_extractor.extract_all_features(url_request.url)
        
        # Make prediction
        prediction_result = model.predict(features)
        
        # Update statistics
        update_stats(prediction_result["is_phishing"])
        
        processing_time = (time.time() - start_time) * 1000
        
        return URLCheckResponse(
            url=url_request.url,
            is_phishing=prediction_result["is_phishing"],
            phishing_probability=prediction_result["phishing_probability"],
            legitimate_probability=prediction_result["legitimate_probability"],
            confidence=prediction_result["confidence"],
            risk_level=get_risk_level(prediction_result["phishing_probability"]),
            timestamp=datetime.now(),
            processing_time_ms=round(processing_time, 2)
        )
    
    except Exception as e:
        logger.error(f"Error processing URL {url_request.url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing URL: {str(e)}"
        )

@app.post("/check-urls-batch", response_model=BatchURLResponse)
@limiter.limit("10/minute")
async def check_urls_batch(request, batch_request: BatchURLRequest, user=Depends(get_current_user)):
    """Check multiple URLs for phishing in a batch request"""
    if not model_stats["loaded"] or model is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded. Please train and load a model first."
        )
    
    start_time = time.time()
    results = []
    phishing_count = 0
    legitimate_count = 0
    
    try:
        for url in batch_request.urls:
            try:
                # Extract features
                features = feature_extractor.extract_all_features(url)
                
                # Make prediction
                prediction_result = model.predict(features)
                
                # Create response
                url_response = URLCheckResponse(
                    url=url,
                    is_phishing=prediction_result["is_phishing"],
                    phishing_probability=prediction_result["phishing_probability"],
                    legitimate_probability=prediction_result["legitimate_probability"],
                    confidence=prediction_result["confidence"],
                    risk_level=get_risk_level(prediction_result["phishing_probability"]),
                    timestamp=datetime.now(),
                    processing_time_ms=0  # Will be set at batch level
                )
                
                results.append(url_response)
                
                if prediction_result["is_phishing"]:
                    phishing_count += 1
                else:
                    legitimate_count += 1
                
                # Update individual stats
                update_stats(prediction_result["is_phishing"])
                
            except Exception as e:
                logger.error(f"Error processing URL {url}: {e}")
                continue
        
        processing_time = (time.time() - start_time) * 1000
        
        return BatchURLResponse(
            results=results,
            total_processed=len(results),
            phishing_count=phishing_count,
            legitimate_count=legitimate_count,
            processing_time_ms=round(processing_time, 2)
        )
    
    except Exception as e:
        logger.error(f"Error processing batch request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing batch request: {str(e)}"
        )

@app.get("/features/{url:path}")
@limiter.limit("30/minute")
async def get_url_features(request, url: str, user=Depends(get_current_user)):
    """Get extracted features for a URL (for debugging/analysis)"""
    if not feature_extractor:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Feature extractor not initialized"
        )
    
    try:
        # Validate URL
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        # Use validators if available, otherwise basic validation
        if VALIDATORS_AVAILABLE:
            is_valid = validators.url(url)
        else:
            is_valid = basic_url_validation(url)
            
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid URL format"
            )
        
        # Extract features
        features = feature_extractor.extract_all_features(url)
        
        return {
            "url": url,
            "features": features,
            "feature_count": len(features),
            "timestamp": datetime.now()
        }
    
    except Exception as e:
        logger.error(f"Error extracting features for {url}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error extracting features: {str(e)}"
        )

# Training endpoint (for model retraining)
@app.post("/train-model")
@limiter.limit("1/hour")
async def train_model_endpoint(
    request,
    background_tasks: BackgroundTasks,
    model_type: str = "xgboost",
    dataset_path: Optional[str] = None,
    user=Depends(get_current_user)
):
    """Trigger model training (background task)"""
    
    # This would typically require admin authentication
    if not dataset_path:
        dataset_path = "data/phishing_dataset.csv"
    
    if not Path(dataset_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Dataset file not found: {dataset_path}"
        )
    
    # Add background training task
    background_tasks.add_task(train_model_background, model_type, dataset_path)
    
    return {
        "message": "Model training started in background",
        "model_type": model_type,
        "dataset_path": dataset_path,
        "status": "training_started"
    }

async def train_model_background(model_type: str, dataset_path: str):
    """Background task for model training"""
    global model, model_stats
    
    try:
        logger.info(f"Starting background training of {model_type} model...")
        
        # This would be the actual training code
        # For now, we'll just simulate it
        await asyncio.sleep(5)  # Simulate training time
        
        logger.info("Model training completed successfully")
        
        # Update global model stats
        model_stats["loaded"] = True
        model_stats["model_type"] = model_type
        
    except Exception as e:
        logger.error(f"Model training failed: {e}")

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.now().isoformat()
    }

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return {
        "error": "Internal server error",
        "status_code": 500,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
