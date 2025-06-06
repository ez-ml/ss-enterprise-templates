# Pinpoint Application
resource "aws_pinpoint_app" "main" {
  name = "${var.project_name}-${var.tenant_id}-${var.environment}"

  limits {
    daily               = 100
    maximum_duration    = 600
    messages_per_second = 50
    total               = 100
  }

  quiet_time {
    end   = "06:00"
    start = "22:00"
  }

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# Lambda function for campaign hooks
resource "aws_lambda_function" "campaign_hook" {
  filename         = "${path.module}/campaign_hook.zip"
  function_name    = "${var.project_name}-${var.tenant_id}-campaign-hook"
  role            = var.lambda_execution_role_arn
  handler         = "index.handler"
  runtime         = "python3.9"
  timeout         = 60

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-campaign-hook"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# Create a dummy zip file for the Lambda function
data "archive_file" "campaign_hook_zip" {
  type        = "zip"
  output_path = "${path.module}/campaign_hook.zip"
  source {
    content = <<EOF
import json

def handler(event, context):
    print(f"Campaign hook triggered: {json.dumps(event)}")
    return {
        'statusCode': 200,
        'body': json.dumps('Campaign hook processed successfully')
    }
EOF
    filename = "index.py"
  }
}

# Pinpoint Email Channel
# Note: Requires SES domain verification and may need special permissions
# resource "aws_pinpoint_email_channel" "email" {
#   application_id = aws_pinpoint_app.main.application_id
#   from_address   = "noreply@${var.project_name}.com"
#   identity       = aws_ses_domain_identity.main.arn
#   enabled        = true
# }

# SES Domain Identity for Pinpoint
resource "aws_ses_domain_identity" "main" {
  domain = "${var.project_name}.com"
}

# Pinpoint SMS Channel
# Note: Requires SMS permissions which may not be available in sandbox accounts
# resource "aws_pinpoint_sms_channel" "sms" {
#   application_id = aws_pinpoint_app.main.application_id
#   enabled        = true
# }

# CloudWatch Log Group for Pinpoint
resource "aws_cloudwatch_log_group" "pinpoint_logs" {
  name              = "/aws/pinpoint/${var.project_name}-${var.tenant_id}-${var.environment}"
  retention_in_days = 14

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}-pinpoint-logs"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# Lambda permission for Pinpoint to invoke the function
resource "aws_lambda_permission" "pinpoint_invoke" {
  statement_id  = "AllowExecutionFromPinpoint"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.campaign_hook.function_name
  principal     = "pinpoint.amazonaws.com"
} 