output "table_name" {
  description = "Name of the recommendations DynamoDB table"
  value       = aws_dynamodb_table.recommendations_cache.name
}

output "table_arn" {
  description = "ARN of the recommendations DynamoDB table"
  value       = aws_dynamodb_table.recommendations_cache.arn
}

output "user_profiles_table_name" {
  description = "Name of the user profiles DynamoDB table"
  value       = aws_dynamodb_table.user_profiles.name
}

output "user_profiles_table_arn" {
  description = "ARN of the user profiles DynamoDB table"
  value       = aws_dynamodb_table.user_profiles.arn
}

output "campaign_tracking_table_name" {
  description = "Name of the campaign tracking DynamoDB table"
  value       = aws_dynamodb_table.campaign_tracking.name
}

output "campaign_tracking_table_arn" {
  description = "ARN of the campaign tracking DynamoDB table"
  value       = aws_dynamodb_table.campaign_tracking.arn
} 