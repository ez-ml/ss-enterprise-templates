# Amazon Personalize Service Role
resource "aws_iam_role" "personalize_service_role" {
  name = "${var.personalize_role_name}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "personalize.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.personalize_role_name}"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

resource "aws_iam_role_policy" "personalize_s3_policy" {
  name = "${var.project_name}-${var.tenant_id}-personalize-s3-policy"
  role = aws_iam_role.personalize_service_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
          "s3:PutObject"
        ]
        Resource = [
          var.s3_bucket_arn,
          "${var.s3_bucket_arn}/*"
        ]
      }
    ]
  })
}

# AppSync Service Role
resource "aws_iam_role" "appsync_service_role" {
  name = "${var.project_name}-${var.tenant_id}-${var.environment}-appsync-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "appsync.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}-appsync-role"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

resource "aws_iam_role_policy" "appsync_dynamodb_policy" {
  name = "${var.project_name}-${var.tenant_id}-appsync-dynamodb-policy"
  role = aws_iam_role.appsync_service_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          var.dynamodb_table_arn,
          "${var.dynamodb_table_arn}/index/*"
        ]
      }
    ]
  })
}

# Step Functions Execution Role
resource "aws_iam_role" "stepfunction_execution_role" {
  name = "${var.project_name}-${var.tenant_id}-${var.environment}-stepfunction-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}-stepfunction-role"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

resource "aws_iam_role_policy" "stepfunction_policy" {
  name = "${var.project_name}-${var.tenant_id}-stepfunction-policy"
  role = aws_iam_role.stepfunction_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "personalize:CreateDatasetImportJob",
          "personalize:CreateSolution",
          "personalize:CreateSolutionVersion",
          "personalize:CreateCampaign",
          "personalize:DescribeDatasetImportJob",
          "personalize:DescribeSolution",
          "personalize:DescribeSolutionVersion",
          "personalize:DescribeCampaign",
          "personalize:ListDatasetImportJobs",
          "personalize:ListSolutions",
          "personalize:ListSolutionVersions",
          "personalize:ListCampaigns"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.s3_bucket_arn,
          "${var.s3_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:DescribeLogGroups"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Additional policy for Step Functions CloudWatch Logs delivery
resource "aws_iam_role_policy" "stepfunction_logs_delivery" {
  name = "${var.project_name}-${var.tenant_id}-stepfunction-logs-delivery"
  role = aws_iam_role.stepfunction_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Resource = "*"
      }
    ]
  })
}

# EventBridge Role
resource "aws_iam_role" "eventbridge_role" {
  name = "${var.project_name}-${var.tenant_id}-${var.environment}-eventbridge-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}-eventbridge-role"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

resource "aws_iam_role_policy" "eventbridge_stepfunction_policy" {
  name = "${var.project_name}-${var.tenant_id}-eventbridge-stepfunction-policy"
  role = aws_iam_role.eventbridge_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "states:StartExecution"
        ]
        Resource = "*"
      }
    ]
  })
}

# Pinpoint Service Role
resource "aws_iam_role" "pinpoint_service_role" {
  name = "${var.project_name}-${var.tenant_id}-${var.environment}-pinpoint-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "pinpoint.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}-pinpoint-role"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

resource "aws_iam_role_policy" "pinpoint_policy" {
  name = "${var.project_name}-${var.tenant_id}-pinpoint-policy"
  role = aws_iam_role.pinpoint_service_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "mobiletargeting:SendMessages",
          "mobiletargeting:SendUsersMessages",
          "mobiletargeting:GetCampaign",
          "mobiletargeting:GetCampaigns",
          "mobiletargeting:CreateCampaign",
          "mobiletargeting:UpdateCampaign"
        ]
        Resource = "*"
      }
    ]
  })
}

# ECS Task Role
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.project_name}-${var.tenant_id}-${var.environment}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}-ecs-task-role"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "${var.project_name}-${var.tenant_id}-ecs-task-policy"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.s3_bucket_arn,
          "${var.s3_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          var.dynamodb_table_arn,
          "${var.dynamodb_table_arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "states:StartExecution",
          "states:DescribeExecution",
          "states:ListExecutions"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "personalize:GetRecommendations",
          "personalize:DescribeCampaign",
          "personalize:ListCampaigns"
        ]
        Resource = "*"
      }
    ]
  })
}

# ECS Execution Role
resource "aws_iam_role" "ecs_execution_role" {
  name = "${var.project_name}-${var.tenant_id}-${var.environment}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}-ecs-execution-role"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Lambda Execution Role for Pinpoint Campaign Hook
resource "aws_iam_role" "lambda_execution_role" {
  name = "${var.project_name}-${var.tenant_id}-${var.environment}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}-lambda-role"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_pinpoint_policy" {
  name = "${var.project_name}-${var.tenant_id}-lambda-pinpoint-policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
} 