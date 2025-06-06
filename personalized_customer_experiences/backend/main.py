"""
Retail Personalization Platform - Backend API
A headless SaaS backend for retail personalization using AWS services.
"""

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
import json
from typing import Optional, List
import boto3
from botocore.exceptions import ClientError
import logging
from datetime import datetime

# Import our service modules
from services.s3_helper import S3Helper
from services.personalize_helper import PersonalizeHelper
from services.stepfunction_helper import StepFunctionHelper
from services.appsync_query import AppSyncQuery
from services.pinpoint_helper import PinpointHelper
from config.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Retail Personalization API",
    description="Headless SaaS backend for retail personalization",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize configuration
config = Config()

# Initialize service helpers
s3_helper = S3Helper(config)
personalize_helper = PersonalizeHelper(config)
stepfunction_helper = StepFunctionHelper(config)
appsync_query = AppSyncQuery(config)
pinpoint_helper = PinpointHelper(config)

# Dependency for API key validation
async def validate_api_key(x_api_key: str = Header(...)):
    """Validate API key from header"""
    if not x_api_key or x_api_key != config.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

# Dependency for tenant ID validation
async def validate_tenant_id(x_tenant_id: str = Header(...)):
    """Validate tenant ID from header"""
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="Tenant ID is required")
    return x_tenant_id

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Retail Personalization API",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "s3": "connected",
            "dynamodb": "connected",
            "personalize": "connected",
            "stepfunctions": "connected",
            "appsync": "connected",
            "pinpoint": "connected"
        }
    }

@app.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_type: str = "interactions",
    api_key: str = Depends(validate_api_key),
    tenant_id: str = Depends(validate_tenant_id)
):
    """
    Upload dataset file to S3
    
    Args:
        file: CSV file containing dataset
        dataset_type: Type of dataset (interactions, users, items)
        api_key: API key for authentication
        tenant_id: Tenant identifier
    """
    try:
        logger.info(f"Uploading {dataset_type} dataset for tenant {tenant_id}")
        
        # Validate file type
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
        # Upload to S3
        s3_key = f"datasets/{tenant_id}/{dataset_type}/{file.filename}"
        s3_url = await s3_helper.upload_file(file, s3_key)
        
        logger.info(f"Dataset uploaded successfully to {s3_url}")
        
        return {
            "message": "Dataset uploaded successfully",
            "s3_url": s3_url,
            "dataset_type": dataset_type,
            "tenant_id": tenant_id,
            "filename": file.filename
        }
        
    except Exception as e:
        logger.error(f"Error uploading dataset: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.post("/train")
async def train_model(
    dataset_location: Optional[str] = None,
    api_key: str = Depends(validate_api_key),
    tenant_id: str = Depends(validate_tenant_id)
):
    """
    Trigger model training via Step Functions
    
    Args:
        dataset_location: S3 location of the dataset (optional)
        api_key: API key for authentication
        tenant_id: Tenant identifier
    """
    try:
        logger.info(f"Starting model training for tenant {tenant_id}")
        
        # If no dataset location provided, use default
        if not dataset_location:
            dataset_location = f"s3://{config.s3_bucket_name}/datasets/{tenant_id}/interactions/interactions.csv"
        
        # Start Step Function execution
        execution_arn = await stepfunction_helper.start_training_workflow(
            tenant_id=tenant_id,
            dataset_location=dataset_location
        )
        
        logger.info(f"Training workflow started: {execution_arn}")
        
        return {
            "message": "Model training started",
            "execution_arn": execution_arn,
            "tenant_id": tenant_id,
            "dataset_location": dataset_location,
            "status": "RUNNING"
        }
        
    except Exception as e:
        logger.error(f"Error starting training: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Training failed: {str(e)}")

@app.get("/recommendations")
async def get_recommendations(
    user_id: str,
    limit: int = 20,
    category: Optional[str] = None,
    api_key: str = Depends(validate_api_key),
    tenant_id: str = Depends(validate_tenant_id)
):
    """
    Get personalized recommendations for a user
    
    Args:
        user_id: User identifier
        limit: Number of recommendations to return
        category: Optional category filter
        api_key: API key for authentication
        tenant_id: Tenant identifier
    """
    try:
        logger.info(f"Getting recommendations for user {user_id}, tenant {tenant_id}")
        
        # Query recommendations from AppSync/DynamoDB
        if category:
            recommendations = await appsync_query.get_recommendations_by_category(
                category=category,
                limit=limit
            )
        else:
            recommendations = await appsync_query.get_recommendations(
                user_id=user_id,
                limit=limit
            )
        
        logger.info(f"Retrieved {len(recommendations.get('items', []))} recommendations")
        
        return {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "recommendations": recommendations,
            "limit": limit,
            "category": category
        }
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Recommendations failed: {str(e)}")

@app.post("/campaign")
async def send_campaign(
    user_ids: List[str],
    message: str,
    subject: str,
    channel: str = "email",
    api_key: str = Depends(validate_api_key),
    tenant_id: str = Depends(validate_tenant_id)
):
    """
    Send marketing campaign via Pinpoint
    
    Args:
        user_ids: List of user identifiers
        message: Campaign message content
        subject: Campaign subject line
        channel: Communication channel (email, sms)
        api_key: API key for authentication
        tenant_id: Tenant identifier
    """
    try:
        logger.info(f"Sending campaign to {len(user_ids)} users for tenant {tenant_id}")
        
        # Send campaign via Pinpoint
        campaign_id = await pinpoint_helper.send_campaign(
            user_ids=user_ids,
            message=message,
            subject=subject,
            channel=channel,
            tenant_id=tenant_id
        )
        
        logger.info(f"Campaign sent successfully: {campaign_id}")
        
        return {
            "message": "Campaign sent successfully",
            "campaign_id": campaign_id,
            "tenant_id": tenant_id,
            "user_count": len(user_ids),
            "channel": channel
        }
        
    except Exception as e:
        logger.error(f"Error sending campaign: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Campaign failed: {str(e)}")

@app.get("/status")
async def get_status(
    execution_arn: Optional[str] = None,
    api_key: str = Depends(validate_api_key),
    tenant_id: str = Depends(validate_tenant_id)
):
    """
    Get status of model training and campaigns
    
    Args:
        execution_arn: Step Function execution ARN (optional)
        api_key: API key for authentication
        tenant_id: Tenant identifier
    """
    try:
        logger.info(f"Getting status for tenant {tenant_id}")
        
        status_info = {
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Get Step Function status if execution ARN provided
        if execution_arn:
            training_status = await stepfunction_helper.get_execution_status(execution_arn)
            status_info["training"] = training_status
        
        # Get Personalize campaign status
        campaigns = await personalize_helper.list_campaigns(tenant_id)
        status_info["campaigns"] = campaigns
        
        # Get recent logs
        logs = await stepfunction_helper.get_recent_logs(tenant_id)
        status_info["recent_logs"] = logs
        
        return status_info
        
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@app.get("/metrics")
async def get_metrics(
    api_key: str = Depends(validate_api_key),
    tenant_id: str = Depends(validate_tenant_id)
):
    """
    Get system metrics and analytics
    
    Args:
        api_key: API key for authentication
        tenant_id: Tenant identifier
    """
    try:
        logger.info(f"Getting metrics for tenant {tenant_id}")
        
        # Get CloudWatch metrics
        metrics = {
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
            "api_requests": 0,  # Placeholder
            "recommendations_served": 0,  # Placeholder
            "campaigns_sent": 0,  # Placeholder
            "model_accuracy": 0.0,  # Placeholder
            "system_health": "healthy"
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Metrics failed: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    ) 