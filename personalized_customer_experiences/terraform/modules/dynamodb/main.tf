# DynamoDB Table for recommendation cache
resource "aws_dynamodb_table" "recommendations_cache" {
  name           = "${var.project_name}-${var.tenant_id}-${var.environment}-recommendations"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"
  range_key      = "item_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "item_id"
    type = "S"
  }

  attribute {
    name = "category"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "N"
  }

  # Global Secondary Index for category-based queries
  global_secondary_index {
    name     = "CategoryIndex"
    hash_key = "category"
    range_key = "timestamp"
    projection_type = "ALL"
  }

  # Global Secondary Index for timestamp-based queries
  global_secondary_index {
    name     = "TimestampIndex"
    hash_key = "timestamp"
    projection_type = "KEYS_ONLY"
  }

  # TTL for automatic cleanup of old recommendations
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  # Point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Server-side encryption
  server_side_encryption {
    enabled = true
  }

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}-recommendations"
    Purpose     = "Recommendation cache"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# DynamoDB Table for user profiles
resource "aws_dynamodb_table" "user_profiles" {
  name           = "${var.project_name}-${var.tenant_id}-${var.environment}-user-profiles"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "segment"
    type = "S"
  }

  attribute {
    name = "last_activity"
    type = "N"
  }

  # Global Secondary Index for segment-based queries
  global_secondary_index {
    name     = "SegmentIndex"
    hash_key = "segment"
    range_key = "last_activity"
    projection_type = "ALL"
  }

  # TTL for inactive users
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  # Point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Server-side encryption
  server_side_encryption {
    enabled = true
  }

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}-user-profiles"
    Purpose     = "User profiles and segments"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# DynamoDB Table for campaign tracking
resource "aws_dynamodb_table" "campaign_tracking" {
  name           = "${var.project_name}-${var.tenant_id}-${var.environment}-campaigns"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "campaign_id"
  range_key      = "user_id"

  attribute {
    name = "campaign_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "N"
  }

  # Global Secondary Index for status-based queries
  global_secondary_index {
    name     = "StatusIndex"
    hash_key = "status"
    range_key = "created_at"
    projection_type = "ALL"
  }

  # TTL for old campaign data
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  # Point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Server-side encryption
  server_side_encryption {
    enabled = true
  }

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}-campaigns"
    Purpose     = "Campaign tracking and analytics"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
} 