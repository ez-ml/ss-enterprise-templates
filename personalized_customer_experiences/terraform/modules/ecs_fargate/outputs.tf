output "cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = aws_ecs_cluster.main.arn
}

output "service_name" {
  description = "Name of the ECS service"
  value       = length(aws_ecs_service.main) > 0 ? aws_ecs_service.main[0].name : ""
}

output "task_definition_arn" {
  description = "ARN of the ECS task definition"
  value       = aws_ecs_task_definition.main.arn
}

output "load_balancer_dns" {
  description = "DNS name of the load balancer"
  value       = length(aws_lb.main) > 0 ? aws_lb.main[0].dns_name : ""
}

output "load_balancer_arn" {
  description = "ARN of the load balancer"
  value       = length(aws_lb.main) > 0 ? aws_lb.main[0].arn : ""
} 