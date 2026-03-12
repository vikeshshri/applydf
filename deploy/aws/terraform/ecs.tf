resource "aws_ecs_cluster" "main" {
  name = var.ecs_cluster_name
}

resource "aws_ecs_service" "backend" {
  name            = var.ecs_service_name
  cluster         = aws_ecs_cluster.main.id
  desired_count   = 1
  launch_type     = "FARGATE"
  # Add task definition, network config, etc.
}
