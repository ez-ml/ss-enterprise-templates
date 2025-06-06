output "rule_arn" {
  description = "ARN of the S3 object created EventBridge rule"
  value       = aws_cloudwatch_event_rule.s3_object_created.arn
}

output "scheduled_rule_arn" {
  description = "ARN of the scheduled retraining EventBridge rule"
  value       = aws_cloudwatch_event_rule.scheduled_retraining.arn
}

output "event_bus_arn" {
  description = "ARN of the custom event bus"
  value       = aws_cloudwatch_event_bus.application_events.arn
}

output "event_bus_name" {
  description = "Name of the custom event bus"
  value       = aws_cloudwatch_event_bus.application_events.name
} 