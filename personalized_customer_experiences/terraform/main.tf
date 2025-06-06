terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      TenantId    = var.tenant_id
    }
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# S3 Module - Data storage and model artifacts
module "s3" {
  source = "./modules/s3"
  
  project_name = var.project_name
  environment  = var.environment
  tenant_id    = var.tenant_id
}

# DynamoDB Module - Real-time recommendation cache
module "dynamodb" {
  source = "./modules/dynamodb"
  
  project_name = var.project_name
  environment  = var.environment
  tenant_id    = var.tenant_id
}

# IAM Module - Service roles and policies
module "iam" {
  source = "./modules/iam"
  
  project_name           = var.project_name
  environment           = var.environment
  tenant_id             = var.tenant_id
  s3_bucket_arn         = module.s3.bucket_arn
  dynamodb_table_arn    = module.dynamodb.table_arn
  personalize_role_name = "PersonalizeServiceRole-${var.project_name}-${var.tenant_id}"
}

# Amazon Personalize Module - ML recommendation engine
# Note: AWS provider doesn't support Personalize resources natively
# module "personalize" {
#   source = "./modules/personalize"
#   
#   project_name     = var.project_name
#   environment      = var.environment
#   tenant_id        = var.tenant_id
#   s3_bucket_name   = module.s3.bucket_name
#   personalize_role = module.iam.personalize_service_role_arn
# }

# AppSync Module - GraphQL API for recommendations
module "appsync" {
  source = "./modules/appsync"
  
  project_name       = var.project_name
  environment        = var.environment
  tenant_id          = var.tenant_id
  dynamodb_table_arn = module.dynamodb.table_arn
  appsync_role_arn   = module.iam.appsync_service_role_arn
}

# Step Functions Module - Workflow orchestration
module "stepfunctions" {
  source = "./modules/stepfunctions"
  
  project_name              = var.project_name
  environment               = var.environment
  tenant_id                 = var.tenant_id
  s3_bucket_name           = module.s3.bucket_name
  # personalize_dataset_group = module.personalize.dataset_group_arn  # Commented out due to unsupported resource
  stepfunction_role_arn    = module.iam.stepfunction_execution_role_arn
}

# EventBridge Module - Event-driven automation
module "eventbridge" {
  source = "./modules/eventbridge"
  
  project_name              = var.project_name
  environment               = var.environment
  tenant_id                 = var.tenant_id
  s3_bucket_name            = module.s3.bucket_name
  stepfunction_arn          = module.stepfunctions.state_machine_arn
  eventbridge_role_arn      = module.iam.eventbridge_role_arn
  # personalize_dataset_group = module.personalize.dataset_group_arn  # Commented out due to unsupported resource
}

# Pinpoint Module - Marketing campaign delivery
module "pinpoint" {
  source = "./modules/pinpoint"
  
  project_name              = var.project_name
  environment               = var.environment
  tenant_id                 = var.tenant_id
  pinpoint_role_arn         = module.iam.pinpoint_service_role_arn
  lambda_execution_role_arn = module.iam.lambda_execution_role_arn
}

# ECS Fargate Module - Containerized microservices
module "ecs_fargate" {
  source = "./modules/ecs_fargate"
  
  project_name    = var.project_name
  environment     = var.environment
  tenant_id       = var.tenant_id
  ecs_task_role   = module.iam.ecs_task_role_arn
  ecs_execution_role = module.iam.ecs_execution_role_arn
  subnets         = var.subnet_ids
  security_groups = var.security_group_ids
}

# Athena Module - Data analytics and querying
module "athena" {
  source = "./modules/athena"
  
  project_name   = var.project_name
  environment    = var.environment
  tenant_id      = var.tenant_id
  s3_bucket_name = module.s3.bucket_name
}

# Monitoring Module - CloudWatch dashboards and alarms
module "monitoring" {
  source = "./modules/monitoring"
  
  project_name         = var.project_name
  environment          = var.environment
  tenant_id            = var.tenant_id
  appsync_api_id       = module.appsync.api_id
  stepfunction_arn     = module.stepfunctions.state_machine_arn
  ecs_cluster_name     = module.ecs_fargate.cluster_name
  ecs_service_name     = module.ecs_fargate.service_name
  dynamodb_table_name  = module.dynamodb.table_name
} 