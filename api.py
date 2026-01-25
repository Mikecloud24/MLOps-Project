"""FastAPI inference server for churn prediction"""
import os
import logging
import pickle
import time
from contextlib import asynccontextmanager
from typing import Optional

import numpy as np
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi.responses import Response

# Configure logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('api_request_duration_seconds', 'Request duration', ['method', 'endpoint'])
PREDICTION_COUNT = Counter('predictions_total', 'Total predictions made', ['prediction'])
MODEL_LOAD_TIME = Gauge('model_load_time_seconds', 'Time taken to load model')
ACTIVE_REQUESTS = Gauge('active_requests', 'Number of active requests')

# Global model variable
model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    global model
    model_path = os.getenv('MODEL_PATH', 'models/churn_model.pkl')
    
    logger.info(f"Loading model from {model_path}")
    start_time = time.time()
    
    try:
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        
        load_time = time.time() - start_time
        MODEL_LOAD_TIME.set(load_time)
        logger.info(f"Model loaded successfully in {load_time:.2f} seconds")
    except FileNotFoundError:
        logger.error(f"Model file not found at {model_path}")
        raise
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")

app = FastAPI(
    title="Churn Prediction API",
    description="ML model API for customer churn prediction",
    version="1.0.0",
    lifespan=lifespan
)

class CustomerData(BaseModel):
    age: int = Field(..., ge=18, le=120, description="Customer age")
    tenure_months: int = Field(..., ge=0, le=240, description="Months as customer")
    monthly_charges: float = Field(..., ge=0, le=1000, description="Monthly charges in dollars")
    total_charges: float = Field(..., ge=0, description="Total charges in dollars")
    num_support_calls: int = Field(..., ge=0, le=100, description="Number of support calls")
    
    @validator('total_charges')
    def validate_total_charges(cls, v, values):
        if 'tenure_months' in values and 'monthly_charges' in values:
            if v < values['monthly_charges'] * 0.5:  # Basic sanity check
                raise ValueError('Total charges seems too low for the tenure and monthly charges')
        return v

class PredictionResponse(BaseModel):
    churn: int
    churn_probability: float
    confidence: str
    request_id: str

class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware to track request metrics"""
    ACTIVE_REQUESTS.inc()
    start_time = time.time()
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    ACTIVE_REQUESTS.dec()
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )

@app.get("/health", response_model=HealthResponse)
def health():
    """Health check endpoint"""
    return {
        "status": "healthy" if model is not None else "unhealthy",
        "model_loaded": model is not None,
        "version": "1.0.0"
    }

@app.get("/readiness")
def readiness():
    """Readiness check endpoint"""
    if model is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "ready"}

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=generate_latest(), media_type="text/plain")

@app.post("/predict", response_model=PredictionResponse)
def predict(data: CustomerData, request: Request):
    """Make churn prediction"""
    if model is None:
        logger.error("Prediction attempted with no model loaded")
        raise HTTPException(status_code=503, detail="Model not available")
    
    try:
        # Prepare features
        features = np.array([[
            data.age,
            data.tenure_months,
            data.monthly_charges,
            data.total_charges,
            data.num_support_calls
        ]])
        
        # Make prediction
        prediction = int(model.predict(features)[0])
        probability = float(model.predict_proba(features)[0][1])
        
        # Determine confidence level
        if probability > 0.8 or probability < 0.2:
            confidence = "high"
        elif probability > 0.6 or probability < 0.4:
            confidence = "medium"
        else:
            confidence = "low"
        
        # Track metrics
        PREDICTION_COUNT.labels(prediction=prediction).inc()
        
        # Generate request ID
        request_id = f"{int(time.time())}-{id(request)}"
        
        logger.info(f"Prediction made: churn={prediction}, probability={probability:.3f}, request_id={request_id}")
        
        return {
            "churn": prediction,
            "churn_probability": probability,
            "confidence": confidence,
            "request_id": request_id
        }
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "Churn Prediction API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "readiness": "/readiness",
            "predict": "/predict",
            "metrics": "/metrics",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level=LOG_LEVEL.lower())