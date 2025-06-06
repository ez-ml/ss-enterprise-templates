# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.tenant_id}-${var.environment}"

  dashboard_body = jsonencode({
    widgets = concat([
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/AppSync", "4XXError", "GraphQLAPIId", var.appsync_api_id],
            [".", "5XXError", ".", "."],
            [".", "Latency", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "AppSync Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", var.dynamodb_table_name],
            [".", "ConsumedWriteCapacityUnits", ".", "."],
            [".", "ThrottledRequests", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "DynamoDB Metrics"
          period  = 300
        }
      }
    ], var.ecs_service_name != "" ? [
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ServiceName", var.ecs_service_name, "ClusterName", var.ecs_cluster_name],
            [".", "MemoryUtilization", ".", ".", ".", "."]
          ]
          view    = "timeSeries"
          stacked = false
          region  = data.aws_region.current.name
          title   = "ECS Metrics"
          period  = 300
        }
      }
    ] : [])
  })
}

# Get current region
data "aws_region" "current" {}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "main" {
  name              = "/aws/${var.project_name}/${var.tenant_id}/${var.environment}"
  retention_in_days = 14

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}-logs"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# CloudWatch Alarm for AppSync Errors
resource "aws_cloudwatch_metric_alarm" "appsync_errors" {
  alarm_name          = "${var.project_name}-${var.tenant_id}-appsync-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "4XXError"
  namespace           = "AWS/AppSync"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors AppSync 4XX errors"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    GraphQLAPIId = var.appsync_api_id
  }

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-appsync-errors"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# CloudWatch Alarm for Step Functions Failures
resource "aws_cloudwatch_metric_alarm" "stepfunction_failures" {
  alarm_name          = "${var.project_name}-${var.tenant_id}-stepfunction-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ExecutionsFailed"
  namespace           = "AWS/States"
  period              = "300"
  statistic           = "Sum"
  threshold           = "0"
  alarm_description   = "This metric monitors Step Functions execution failures"
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    StateMachineArn = var.stepfunction_arn
  }

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-stepfunction-failures"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# SNS Topic for Alerts
resource "aws_sns_topic" "alerts" {
  name = "${var.project_name}-${var.tenant_id}-${var.environment}-alerts"

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}-alerts"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# SNS Topic Subscription (placeholder)
resource "aws_sns_topic_subscription" "email_alerts" {
  count     = var.monitoring_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.monitoring_email
} 