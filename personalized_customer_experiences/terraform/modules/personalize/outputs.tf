output "dataset_group_arn" {
  description = "ARN of the Personalize dataset group"
  value       = aws_personalize_dataset_group.main.arn
}

output "dataset_group_name" {
  description = "Name of the Personalize dataset group"
  value       = aws_personalize_dataset_group.main.name
}

output "interactions_dataset_arn" {
  description = "ARN of the interactions dataset"
  value       = aws_personalize_dataset.interactions.arn
}

output "users_dataset_arn" {
  description = "ARN of the users dataset"
  value       = aws_personalize_dataset.users.arn
}

output "items_dataset_arn" {
  description = "ARN of the items dataset"
  value       = aws_personalize_dataset.items.arn
}

output "interactions_schema_arn" {
  description = "ARN of the interactions schema"
  value       = aws_personalize_schema.interactions.arn
}

output "users_schema_arn" {
  description = "ARN of the users schema"
  value       = aws_personalize_schema.users.arn
}

output "items_schema_arn" {
  description = "ARN of the items schema"
  value       = aws_personalize_schema.items.arn
} 