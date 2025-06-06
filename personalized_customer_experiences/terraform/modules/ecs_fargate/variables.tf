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

variable "ecs_task_role" {
  description = "ARN of the ECS task role"
  type        = string
}

variable "ecs_execution_role" {
  description = "ARN of the ECS execution role"
  type        = string
}

variable "subnets" {
  description = "List of subnet IDs"
  type        = list(string)
  default     = []
}

variable "security_groups" {
  description = "List of security group IDs"
  type        = list(string)
  default     = []
} 