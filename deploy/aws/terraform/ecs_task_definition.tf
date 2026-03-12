resource "aws_ecs_task_definition" "backend" {
  family                   = "applydf-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = "arn:aws:iam::${var.aws_account_id}:role/ecsTaskExecutionRole"
  container_definitions    = jsonencode([
    {
      name      = "backend"
      image     = "${var.ecr_backend_repository}:latest"
      essential = true
      portMappings = [{ containerPort = 8000, hostPort = 8000 }]
      environment = []
    }
  ])
}
