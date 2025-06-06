# EventBridge Rule for S3 Object Creation
resource "aws_cloudwatch_event_rule" "s3_object_created" {
  name        = "${var.project_name}-${var.tenant_id}-${var.environment}-s3-object-created"
  description = "Trigger ML workflow when new data is uploaded to S3"

  event_pattern = jsonencode({
    source      = ["aws.s3"]
    detail-type = ["Object Created"]
    detail = {
      bucket = {
        name = [var.s3_bucket_name]
      }
      object = {
        key = [
          {
            prefix = "datasets/"
          }
        ]
      }
    }
  })

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}-s3-object-created"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# EventBridge Target for Step Functions
resource "aws_cloudwatch_event_target" "stepfunction_target" {
  rule      = aws_cloudwatch_event_rule.s3_object_created.name
  target_id = "StepFunctionTarget"
  arn       = var.stepfunction_arn
  role_arn  = var.eventbridge_role_arn

  input_transformer {
    input_paths = {
      bucket = "$.detail.bucket.name"
      key    = "$.detail.object.key"
    }
    input_template = jsonencode({
      dataLocation = "s3://<bucket>/<key>"
      datasetArn   = "${var.personalize_dataset_group}/datasets/interactions"
      jobName      = "${var.project_name}-${var.tenant_id}-import-<aws.events.event.ingestion-time>"
      solutionName = "${var.project_name}-${var.tenant_id}-solution-<aws.events.event.ingestion-time>"
      campaignName = "${var.project_name}-${var.tenant_id}-campaign-<aws.events.event.ingestion-time>"
      datasetGroupArn = var.personalize_dataset_group
      personalizeRoleArn = var.eventbridge_role_arn
    })
  }
}

# EventBridge Rule for Scheduled Model Retraining
resource "aws_cloudwatch_event_rule" "scheduled_retraining" {
  name                = "${var.project_name}-${var.tenant_id}-${var.environment}-scheduled-retraining"
  description         = "Scheduled model retraining"
  schedule_expression = "rate(7 days)"

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}-scheduled-retraining"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# EventBridge Target for Scheduled Retraining
resource "aws_cloudwatch_event_target" "scheduled_retraining_target" {
  rule      = aws_cloudwatch_event_rule.scheduled_retraining.name
  target_id = "ScheduledRetrainingTarget"
  arn       = var.stepfunction_arn
  role_arn  = var.eventbridge_role_arn

  input = jsonencode({
    dataLocation = "s3://${var.s3_bucket_name}/datasets/interactions.csv"
    datasetArn   = "${var.personalize_dataset_group}/datasets/interactions"
    jobName      = "${var.project_name}-${var.tenant_id}-scheduled-retrain"
    solutionName = "${var.project_name}-${var.tenant_id}-solution-scheduled"
    campaignName = "${var.project_name}-${var.tenant_id}-campaign-scheduled"
    datasetGroupArn = var.personalize_dataset_group
    personalizeRoleArn = var.eventbridge_role_arn
  })
}

# EventBridge Custom Bus for Application Events
resource "aws_cloudwatch_event_bus" "application_events" {
  name = "${var.project_name}-${var.tenant_id}-${var.environment}-events"

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}-events"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# EventBridge Rule for Application Events
resource "aws_cloudwatch_event_rule" "application_events" {
  name           = "${var.project_name}-${var.tenant_id}-${var.environment}-app-events"
  description    = "Handle application-specific events"
  event_bus_name = aws_cloudwatch_event_bus.application_events.name

  event_pattern = jsonencode({
    source      = ["retail.personalization"]
    detail-type = ["Model Training Complete", "Campaign Status Change"]
  })

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}-app-events"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
} 