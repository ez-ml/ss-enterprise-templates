output "app_id" {
  description = "Pinpoint application ID"
  value       = aws_pinpoint_app.main.application_id
}

output "app_arn" {
  description = "Pinpoint application ARN"
  value       = aws_pinpoint_app.main.arn
}

output "app_name" {
  description = "Pinpoint application name"
  value       = aws_pinpoint_app.main.name
} 