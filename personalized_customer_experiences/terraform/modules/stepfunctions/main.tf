# Step Functions State Machine for ML Workflow
resource "aws_sfn_state_machine" "ml_workflow" {
  name     = "${var.project_name}-${var.tenant_id}-${var.environment}-ml-workflow"
  role_arn = var.stepfunction_role_arn

  definition = jsonencode({
    Comment = "ML Workflow for Retail Personalization"
    StartAt = "CheckDatasetExists"
    States = {
      CheckDatasetExists = {
        Type = "Task"
        Resource = "arn:aws:states:::aws-sdk:personalize:describeDataset"
        Parameters = {
          "DatasetArn.$" = "$.datasetArn"
        }
        Catch = [
          {
            ErrorEquals = ["States.TaskFailed"]
            Next = "DatasetNotFound"
          }
        ]
        Next = "CreateDatasetImportJob"
      }
      
      DatasetNotFound = {
        Type = "Fail"
        Cause = "Dataset does not exist"
        Error = "DatasetNotFound"
      }
      
      CreateDatasetImportJob = {
        Type = "Task"
        Resource = "arn:aws:states:::aws-sdk:personalize:createDatasetImportJob"
        Parameters = {
          "JobName.$" = "$.jobName"
          "DatasetArn.$" = "$.datasetArn"
          "DataSource" = {
            "DataLocation.$" = "$.dataLocation"
          }
          "RoleArn.$" = "$.personalizeRoleArn"
        }
        Next = "WaitForDatasetImport"
      }
      
      WaitForDatasetImport = {
        Type = "Wait"
        Seconds = 60
        Next = "CheckDatasetImportStatus"
      }
      
      CheckDatasetImportStatus = {
        Type = "Task"
        Resource = "arn:aws:states:::aws-sdk:personalize:describeDatasetImportJob"
        Parameters = {
          "DatasetImportJobArn.$" = "$.DatasetImportJobArn"
        }
        Next = "IsDatasetImportComplete"
      }
      
      IsDatasetImportComplete = {
        Type = "Choice"
        Choices = [
          {
            Variable = "$.Status"
            StringEquals = "ACTIVE"
            Next = "CreateSolution"
          },
          {
            Variable = "$.Status"
            StringEquals = "CREATE FAILED"
            Next = "DatasetImportFailed"
          }
        ]
        Default = "WaitForDatasetImport"
      }
      
      DatasetImportFailed = {
        Type = "Fail"
        Cause = "Dataset import failed"
        Error = "DatasetImportFailed"
      }
      
      CreateSolution = {
        Type = "Task"
        Resource = "arn:aws:states:::aws-sdk:personalize:createSolution"
        Parameters = {
          "Name.$" = "$.solutionName"
          "DatasetGroupArn.$" = "$.datasetGroupArn"
          "RecipeArn" = "arn:aws:personalize:::recipe/aws-user-personalization"
        }
        Next = "CreateSolutionVersion"
      }
      
      CreateSolutionVersion = {
        Type = "Task"
        Resource = "arn:aws:states:::aws-sdk:personalize:createSolutionVersion"
        Parameters = {
          "SolutionArn.$" = "$.SolutionArn"
        }
        Next = "WaitForSolutionVersion"
      }
      
      WaitForSolutionVersion = {
        Type = "Wait"
        Seconds = 300
        Next = "CheckSolutionVersionStatus"
      }
      
      CheckSolutionVersionStatus = {
        Type = "Task"
        Resource = "arn:aws:states:::aws-sdk:personalize:describeSolutionVersion"
        Parameters = {
          "SolutionVersionArn.$" = "$.SolutionVersionArn"
        }
        Next = "IsSolutionVersionComplete"
      }
      
      IsSolutionVersionComplete = {
        Type = "Choice"
        Choices = [
          {
            Variable = "$.Status"
            StringEquals = "ACTIVE"
            Next = "CreateCampaign"
          },
          {
            Variable = "$.Status"
            StringEquals = "CREATE FAILED"
            Next = "SolutionVersionFailed"
          }
        ]
        Default = "WaitForSolutionVersion"
      }
      
      SolutionVersionFailed = {
        Type = "Fail"
        Cause = "Solution version creation failed"
        Error = "SolutionVersionFailed"
      }
      
      CreateCampaign = {
        Type = "Task"
        Resource = "arn:aws:states:::aws-sdk:personalize:createCampaign"
        Parameters = {
          "Name.$" = "$.campaignName"
          "SolutionVersionArn.$" = "$.SolutionVersionArn"
          "MinProvisionedTPS" = 1
        }
        Next = "WaitForCampaign"
      }
      
      WaitForCampaign = {
        Type = "Wait"
        Seconds = 60
        Next = "CheckCampaignStatus"
      }
      
      CheckCampaignStatus = {
        Type = "Task"
        Resource = "arn:aws:states:::aws-sdk:personalize:describeCampaign"
        Parameters = {
          "CampaignArn.$" = "$.CampaignArn"
        }
        Next = "IsCampaignComplete"
      }
      
      IsCampaignComplete = {
        Type = "Choice"
        Choices = [
          {
            Variable = "$.Status"
            StringEquals = "ACTIVE"
            Next = "WorkflowComplete"
          },
          {
            Variable = "$.Status"
            StringEquals = "CREATE FAILED"
            Next = "CampaignFailed"
          }
        ]
        Default = "WaitForCampaign"
      }
      
      CampaignFailed = {
        Type = "Fail"
        Cause = "Campaign creation failed"
        Error = "CampaignFailed"
      }
      
      WorkflowComplete = {
        Type = "Succeed"
        Comment = "ML workflow completed successfully"
      }
    }
  })

  # Temporarily commenting out logging configuration to resolve permission issues
  # logging_configuration {
  #   log_destination        = "${aws_cloudwatch_log_group.stepfunction_logs.arn}:*"
  #   include_execution_data = true
  #   level                  = "ALL"
  # }

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}-ml-workflow"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# CloudWatch Log Group for Step Functions
resource "aws_cloudwatch_log_group" "stepfunction_logs" {
  name              = "/aws/stepfunctions/${var.project_name}-${var.tenant_id}-${var.environment}"
  retention_in_days = 14

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}-stepfunction-logs"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
} 