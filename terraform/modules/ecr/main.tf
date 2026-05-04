variable "project" { type = string }
variable "environment" { type = string }
variable "services" {
  type    = list(string)
  default = []
}

resource "aws_ecr_repository" "services" {
  for_each             = toset(var.services)
  name                 = "${var.project}/${each.value}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Project     = var.project
    Environment = var.environment
    Service     = each.value
  }
}

# Keep only the last 10 images to save storage costs
resource "aws_ecr_lifecycle_policy" "services" {
  for_each   = toset(var.services)
  repository = "${var.project}/${each.value}"

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}

output "repository_urls" {
  value = { for k, v in aws_ecr_repository.services : k => v.repository_url }
}
