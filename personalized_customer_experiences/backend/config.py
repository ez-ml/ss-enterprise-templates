import os
from typing import Optional
from pydantic import BaseSettings, validator
import boto3
from botocore.config import Config


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Configuration
    api_title: str = "Retail Personalization API"
    api_version: str = "1.0.0"
    api_description: str = "Headless SaaS backend for retail personalization"
    debug: bool = False
    
    # Authentication
    api_key_header: str = "X-API-Key"
    tenant_header: str = "X-Tenant-ID"
    
    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # S3 Configuration
    s3_bucket_name: str
    s3_data_prefix: str = "data"
    s3_models_prefix: str = "models"
    s3_logs_prefix: str = "logs"
    
    # DynamoDB Configuration
    dynamodb_recommendations_table: str
    dynamodb_user_profiles_table: str
    dynamodb_campaign_tracking_table: str
    
    # Personalize Configuration
    personalize_dataset_group_name: str
    personalize_solution_name: str = "retail-recommendations"
    personalize_campaign_name: str = "retail-campaign"
    personalize_event_tracker_name: str = "retail-events"
    
    # AppSync Configuration
    appsync_api_id: str
    appsync_api_url: str
    appsync_api_key: str
    
    # Step Functions Configuration
    stepfunctions_state_machine_arn: str
    
    # EventBridge Configuration
    eventbridge_bus_name: str = "retail-personalization"
    
    # Pinpoint Configuration
    pinpoint_application_id: str
    pinpoint_from_address: str
    
    # ECS Configuration
    ecs_cluster_name: str
    ecs_service_name: str
    
    # Athena Configuration
    athena_workgroup: str = "retail-analytics"
    athena_output_location: str
    
    # CloudWatch Configuration
    cloudwatch_log_group: str = "/aws/lambda/retail-personalization"
    cloudwatch_dashboard_name: str = "RetailPersonalization"
    
    # Rate Limiting
    rate_limit_requests: int = 1000
    rate_limit_window: int = 3600  # 1 hour
    
    # Timeouts (in seconds)
    request_timeout: int = 30
    training_timeout: int = 3600  # 1 hour
    
    @validator('s3_bucket_name')
    def validate_s3_bucket_name(cls, v):
        if not v:
            raise ValueError('S3 bucket name is required')
        return v
    
    @validator('aws_region')
    def validate_aws_region(cls, v):
        valid_regions = [
            'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
            'eu-west-1', 'eu-west-2', 'eu-central-1', 'ap-southeast-1',
            'ap-southeast-2', 'ap-northeast-1'
        ]
        if v not in valid_regions:
            raise ValueError(f'Invalid AWS region. Must be one of: {valid_regions}')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class AWSConfig:
    """AWS service configuration and client management."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.config = Config(
            region_name=settings.aws_region,
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            max_pool_connections=50
        )
        
        # Session configuration
        session_kwargs = {}
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            session_kwargs.update({
                'aws_access_key_id': settings.aws_access_key_id,
                'aws_secret_access_key': settings.aws_secret_access_key
            })
        
        self.session = boto3.Session(**session_kwargs)
    
    @property
    def s3_client(self):
        """Get S3 client."""
        return self.session.client('s3', config=self.config)
    
    @property
    def dynamodb_client(self):
        """Get DynamoDB client."""
        return self.session.client('dynamodb', config=self.config)
    
    @property
    def dynamodb_resource(self):
        """Get DynamoDB resource."""
        return self.session.resource('dynamodb', config=self.config)
    
    @property
    def personalize_client(self):
        """Get Personalize client."""
        return self.session.client('personalize', config=self.config)
    
    @property
    def personalize_runtime_client(self):
        """Get Personalize Runtime client."""
        return self.session.client('personalize-runtime', config=self.config)
    
    @property
    def personalize_events_client(self):
        """Get Personalize Events client."""
        return self.session.client('personalize-events', config=self.config)
    
    @property
    def stepfunctions_client(self):
        """Get Step Functions client."""
        return self.session.client('stepfunctions', config=self.config)
    
    @property
    def eventbridge_client(self):
        """Get EventBridge client."""
        return self.session.client('events', config=self.config)
    
    @property
    def pinpoint_client(self):
        """Get Pinpoint client."""
        return self.session.client('pinpoint', config=self.config)
    
    @property
    def ecs_client(self):
        """Get ECS client."""
        return self.session.client('ecs', config=self.config)
    
    @property
    def athena_client(self):
        """Get Athena client."""
        return self.session.client('athena', config=self.config)
    
    @property
    def cloudwatch_client(self):
        """Get CloudWatch client."""
        return self.session.client('cloudwatch', config=self.config)
    
    @property
    def logs_client(self):
        """Get CloudWatch Logs client."""
        return self.session.client('logs', config=self.config)


# Global settings instance
settings = Settings()
aws_config = AWSConfig(settings)


# API Key validation (in production, this would be in a database)
VALID_API_KEYS = {
    "demo-key-123": {
        "tenant_id": "demo-tenant",
        "name": "Demo Client",
        "permissions": ["read", "write", "train"],
        "rate_limit": 1000
    },
    "test-key-456": {
        "tenant_id": "test-tenant", 
        "name": "Test Client",
        "permissions": ["read"],
        "rate_limit": 100
    }
}


def get_tenant_from_api_key(api_key: str) -> Optional[dict]:
    """Get tenant information from API key."""
    return VALID_API_KEYS.get(api_key)


def validate_tenant_permission(api_key: str, permission: str) -> bool:
    """Validate if API key has required permission."""
    tenant_info = get_tenant_from_api_key(api_key)
    if not tenant_info:
        return False
    return permission in tenant_info.get("permissions", []) 