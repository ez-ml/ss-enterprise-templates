# Athena Database
resource "aws_athena_database" "main" {
  name   = "${replace(var.project_name, "-", "_")}_${replace(var.tenant_id, "-", "_")}_${var.environment}"
  bucket = var.s3_bucket_name

  encryption_configuration {
    encryption_option = "SSE_S3"
  }
}

# Athena Workgroup
resource "aws_athena_workgroup" "main" {
  name = "${var.project_name}-${var.tenant_id}-${var.environment}"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${var.s3_bucket_name}/athena-results/"

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }
  }

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# Athena Named Query for common analytics
resource "aws_athena_named_query" "user_interactions" {
  name      = "user_interactions_analysis"
  database  = aws_athena_database.main.name
  workgroup = aws_athena_workgroup.main.id
  query     = <<EOF
SELECT 
    user_id,
    COUNT(*) as interaction_count,
    COUNT(DISTINCT item_id) as unique_items,
    AVG(event_value) as avg_event_value
FROM interactions 
WHERE event_type = 'purchase'
GROUP BY user_id
ORDER BY interaction_count DESC
LIMIT 100;
EOF

  description = "Analyze user interaction patterns"
}

# Athena Named Query for item popularity
resource "aws_athena_named_query" "item_popularity" {
  name      = "item_popularity_analysis"
  database  = aws_athena_database.main.name
  workgroup = aws_athena_workgroup.main.id
  query     = <<EOF
SELECT 
    item_id,
    COUNT(*) as interaction_count,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(event_value) as avg_event_value
FROM interactions 
WHERE event_type IN ('view', 'purchase', 'add_to_cart')
GROUP BY item_id
ORDER BY interaction_count DESC
LIMIT 100;
EOF

  description = "Analyze item popularity and engagement"
} 