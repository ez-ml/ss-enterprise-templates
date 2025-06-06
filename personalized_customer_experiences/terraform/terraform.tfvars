# AWS Configuration
aws_region = "us-east-1"

# Project Configuration
project_name = "retail-personalization"
environment  = "dev"
tenant_id    = "acme-corp"

# Network Configuration (Update with your VPC details)
# subnet_ids         = ["subnet-12345678", "subnet-87654321"]
# security_group_ids = ["sg-12345678"]

# Resource Configuration
enable_deletion_protection = false  # Set to true for production
backup_retention_days     = 7       # Reduce for dev environment
cost_budget_limit         = 500     # Monthly budget in USD

# Monitoring Configuration
monitoring_email = "admin@example.com"
log_retention_days = 7  # Reduce for dev environment

# Performance Configuration
api_throttle_rate  = 100   # Requests per second
api_throttle_burst = 200   # Burst limit

# DynamoDB Configuration
dynamodb_billing_mode = "PAY_PER_REQUEST"  # Cost-effective for variable workloads

# S3 Configuration
s3_versioning_enabled = true
s3_lifecycle_enabled  = true

# ECS Configuration
ecs_cpu           = 256    # Minimum for dev
ecs_memory        = 512    # Minimum for dev
ecs_desired_count = 1      # Single instance for dev

# Auto Scaling Configuration
enable_auto_scaling       = false  # Disable for dev
min_capacity             = 1
max_capacity             = 3
target_cpu_utilization   = 70

# Feature Flags
enable_vpc_endpoints      = false  # Enable for production
enable_xray_tracing      = true
enable_container_insights = true

# Amazon Personalize Configuration
personalize_recipe_arn = "arn:aws:personalize:::recipe/aws-user-personalization"

# Additional Tags
tags = {
  Owner       = "DevOps Team"
  CostCenter  = "Engineering"
  Application = "Retail Personalization"
} 