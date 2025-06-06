# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.tenant_id}-${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  count              = length(var.subnets) > 0 ? 1 : 0
  name               = "${substr(var.project_name, 0, 10)}-${substr(var.tenant_id, 0, 8)}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = var.security_groups
  subnets            = var.subnets

  enable_deletion_protection = false

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-alb"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# Target Group
resource "aws_lb_target_group" "main" {
  count       = length(var.subnets) > 0 ? 1 : 0
  name        = "${substr(var.project_name, 0, 10)}-${substr(var.tenant_id, 0, 8)}-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = data.aws_subnet.first[0].vpc_id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-tg"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# Get VPC ID from subnet
data "aws_subnet" "first" {
  count = length(var.subnets) > 0 ? 1 : 0
  id    = var.subnets[0]
}

# Load Balancer Listener
resource "aws_lb_listener" "main" {
  count             = length(var.subnets) > 0 ? 1 : 0
  load_balancer_arn = aws_lb.main[0].arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main[0].arn
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "main" {
  family                   = "${var.project_name}-${var.tenant_id}-${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = var.ecs_execution_role
  task_role_arn           = var.ecs_task_role

  container_definitions = jsonencode([
    {
      name  = "backend-api"
      image = "nginx:latest"  # Placeholder - will be replaced with actual backend image
      portMappings = [
        {
          containerPort = 3000
          hostPort      = 3000
          protocol      = "tcp"
        }
      ]
      essential = true
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs_logs.name
          awslogs-region        = data.aws_region.current.name
          awslogs-stream-prefix = "ecs"
        }
      }
      environment = [
        {
          name  = "NODE_ENV"
          value = var.environment
        },
        {
          name  = "PROJECT_NAME"
          value = var.project_name
        },
        {
          name  = "TENANT_ID"
          value = var.tenant_id
        }
      ]
    }
  ])

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# Get current region
data "aws_region" "current" {}

# CloudWatch Log Group for ECS
resource "aws_cloudwatch_log_group" "ecs_logs" {
  name              = "/ecs/${var.project_name}-${var.tenant_id}-${var.environment}"
  retention_in_days = 14

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}-ecs-logs"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
}

# ECS Service
resource "aws_ecs_service" "main" {
  count           = length(var.subnets) > 0 ? 1 : 0
  name            = "${var.project_name}-${var.tenant_id}-${var.environment}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.main.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    security_groups  = var.security_groups
    subnets          = var.subnets
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.main[0].arn
    container_name   = "backend-api"
    container_port   = 3000
  }

  depends_on = [aws_lb_listener.main]

  tags = {
    Name        = "${var.project_name}-${var.tenant_id}-${var.environment}"
    Project     = var.project_name
    Environment = var.environment
    TenantId    = var.tenant_id
  }
} 