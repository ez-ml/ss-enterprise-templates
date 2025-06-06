# S3 Outputs
output "s3_bucket_name" {
  description = "Name of the S3 bucket for data storage"
  value       = module.s3.bucket_name
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = module.s3.bucket_arn
}

output "s3_bucket_domain_name" {
  description = "Domain name of the S3 bucket"
  value       = module.s3.bucket_domain_name
}

# DynamoDB Outputs
output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for recommendations cache"
  value       = module.dynamodb.table_name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table"
  value       = module.dynamodb.table_arn
}

# AppSync Outputs
output "appsync_api_id" {
  description = "AppSync API ID"
  value       = module.appsync.api_id
}

output "appsync_api_url" {
  description = "AppSync GraphQL API URL"
  value       = module.appsync.graphql_url
}

output "appsync_api_key" {
  description = "AppSync API Key"
  value       = module.appsync.api_key
  sensitive   = true
}

# Amazon Personalize Outputs
# output "personalize_dataset_group_arn" {
#   description = "Amazon Personalize dataset group ARN"
#   value       = module.personalize.dataset_group_arn
# }

# output "personalize_dataset_group_name" {
#   description = "Amazon Personalize dataset group name"
#   value       = module.personalize.dataset_group_name
# }

# output "personalize_interactions_dataset_arn" {
#   description = "Amazon Personalize interactions dataset ARN"
#   value       = module.personalize.interactions_dataset_arn
# }

# output "personalize_users_dataset_arn" {
#   description = "Amazon Personalize users dataset ARN"
#   value       = module.personalize.users_dataset_arn
# }

# output "personalize_items_dataset_arn" {
#   description = "Amazon Personalize items dataset ARN"
#   value       = module.personalize.items_dataset_arn
# }

# Step Functions Outputs
output "stepfunction_arn" {
  description = "Step Functions state machine ARN"
  value       = module.stepfunctions.state_machine_arn
}

output "stepfunction_name" {
  description = "Step Functions state machine name"
  value       = module.stepfunctions.state_machine_name
}

# EventBridge Outputs
output "eventbridge_rule_arn" {
  description = "EventBridge rule ARN"
  value       = module.eventbridge.rule_arn
}

# Pinpoint Outputs
output "pinpoint_app_id" {
  description = "Pinpoint application ID"
  value       = module.pinpoint.app_id
}

output "pinpoint_app_arn" {
  description = "Pinpoint application ARN"
  value       = module.pinpoint.app_arn
}

# ECS Fargate Outputs
output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs_fargate.cluster_name
}

output "ecs_cluster_arn" {
  description = "ECS cluster ARN"
  value       = module.ecs_fargate.cluster_arn
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = module.ecs_fargate.service_name
}

output "ecs_task_definition_arn" {
  description = "ECS task definition ARN"
  value       = module.ecs_fargate.task_definition_arn
}

output "ecs_load_balancer_dns" {
  description = "ECS load balancer DNS name"
  value       = module.ecs_fargate.load_balancer_dns
}

# Athena Outputs
output "athena_database_name" {
  description = "Athena database name"
  value       = module.athena.database_name
}

output "athena_workgroup_name" {
  description = "Athena workgroup name"
  value       = module.athena.workgroup_name
}

# IAM Outputs
output "personalize_service_role_arn" {
  description = "Amazon Personalize service role ARN"
  value       = module.iam.personalize_service_role_arn
}

output "appsync_service_role_arn" {
  description = "AppSync service role ARN"
  value       = module.iam.appsync_service_role_arn
}

output "ecs_task_role_arn" {
  description = "ECS task role ARN"
  value       = module.iam.ecs_task_role_arn
}

output "ecs_execution_role_arn" {
  description = "ECS execution role ARN"
  value       = module.iam.ecs_execution_role_arn
}

# Monitoring Outputs
output "cloudwatch_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = module.monitoring.dashboard_url
}

output "cloudwatch_log_group_name" {
  description = "CloudWatch log group name"
  value       = module.monitoring.log_group_name
}

# General Outputs
output "aws_region" {
  description = "AWS region where resources are deployed"
  value       = var.aws_region
}

output "project_name" {
  description = "Project name"
  value       = var.project_name
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "tenant_id" {
  description = "Tenant ID"
  value       = var.tenant_id
}

# Backend API Configuration
output "backend_config" {
  description = "Configuration for backend API"
  value = {
    aws_region                    = var.aws_region
    s3_bucket_name               = module.s3.bucket_name
    dynamodb_table_name          = module.dynamodb.table_name
    appsync_api_url              = module.appsync.graphql_url
    appsync_api_key              = module.appsync.api_key
    # personalize_dataset_group_arn = module.personalize.dataset_group_arn  # Commented out due to unsupported resource
    stepfunction_arn             = module.stepfunctions.state_machine_arn
    pinpoint_app_id              = module.pinpoint.app_id
    project_name                 = var.project_name
    tenant_id                    = var.tenant_id
    environment                  = var.environment
  }
  sensitive = true
} 