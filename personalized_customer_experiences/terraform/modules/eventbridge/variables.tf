variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "tenant_id" {
  description = "Unique identifier for the tenant"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket"
  type        = string
}

variable "stepfunction_arn" {
  description = "ARN of the Step Functions state machine"
  type        = string
}

variable "eventbridge_role_arn" {
  description = "ARN of the EventBridge role"
  type        = string
}

variable "personalize_dataset_group" {
  description = "ARN of the Personalize dataset group"
  type        = string
  default     = ""
} 