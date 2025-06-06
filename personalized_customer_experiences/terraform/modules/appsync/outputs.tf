output "api_id" {
  description = "ID of the AppSync GraphQL API"
  value       = aws_appsync_graphql_api.main.id
}

output "api_arn" {
  description = "ARN of the AppSync GraphQL API"
  value       = aws_appsync_graphql_api.main.arn
}

output "graphql_url" {
  description = "URL of the GraphQL endpoint"
  value       = aws_appsync_graphql_api.main.uris["GRAPHQL"]
}

output "api_key" {
  description = "API key for the GraphQL API"
  value       = aws_appsync_api_key.main.key
  sensitive   = true
} 