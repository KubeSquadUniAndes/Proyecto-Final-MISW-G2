locals {
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# ── SNS Topic ─────────────────────────────────────────────────────────────────
resource "aws_sns_topic" "room_availability" {
  name = "${var.project}-room-availability"

  tags = local.common_tags
}

# ── SQS Dead-Letter Queue ─────────────────────────────────────────────────────
resource "aws_sqs_queue" "hospedajes_availability_dlq" {
  name                      = "${var.project}-hospedajes-availability-dlq"
  message_retention_seconds = 1209600 # 14 days — max retention for forensic review

  tags = local.common_tags
}

# ── SQS Main Queue ────────────────────────────────────────────────────────────
resource "aws_sqs_queue" "hospedajes_availability" {
  name                       = "${var.project}-hospedajes-availability"
  visibility_timeout_seconds = var.visibility_timeout_seconds
  message_retention_seconds  = var.message_retention_seconds
  receive_wait_time_seconds  = 20 # long-poll at queue level; reduces empty-receive costs

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.hospedajes_availability_dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = local.common_tags
}

# ── SNS → SQS Subscription ───────────────────────────────────────────────────
resource "aws_sns_topic_subscription" "hospedajes_availability" {
  topic_arn = aws_sns_topic.room_availability.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.hospedajes_availability.arn
}

# ── SQS Queue Policy — allow SNS to send messages ────────────────────────────
resource "aws_sqs_queue_policy" "hospedajes_availability" {
  queue_url = aws_sqs_queue.hospedajes_availability.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowSNSPublish"
      Effect    = "Allow"
      Principal = { Service = "sns.amazonaws.com" }
      Action    = "sqs:SendMessage"
      Resource  = aws_sqs_queue.hospedajes_availability.arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = aws_sns_topic.room_availability.arn
        }
      }
    }]
  })
}

# ── IAM Policy — SNS publish for reservas_ms ─────────────────────────────────
resource "aws_iam_policy" "sns_publish_room_availability" {
  name        = "${var.project}-${var.environment}-sns-publish-room-availability"
  description = "Allow reservas_ms pods to publish booking events to the room-availability SNS topic"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid      = "AllowSNSPublish"
      Effect   = "Allow"
      Action   = ["sns:Publish"]
      Resource = aws_sns_topic.room_availability.arn
    }]
  })
}

resource "aws_iam_role_policy_attachment" "nodes_sns_publish" {
  role       = var.node_role_name
  policy_arn = aws_iam_policy.sns_publish_room_availability.arn
}

# ── IAM Policy — SQS consume for hospedajes_ms ───────────────────────────────
resource "aws_iam_policy" "sqs_consume_room_availability" {
  name        = "${var.project}-${var.environment}-sqs-consume-room-availability"
  description = "Allow hospedajes_ms pods to receive and delete messages from the room-availability queue"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowSQSConsume"
      Effect = "Allow"
      Action = [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
      ]
      Resource = aws_sqs_queue.hospedajes_availability.arn
    }]
  })
}

resource "aws_iam_role_policy_attachment" "nodes_sqs_consume" {
  role       = var.node_role_name
  policy_arn = aws_iam_policy.sqs_consume_room_availability.arn
}

# ── IRSA Role — hospedajes_ms SQS consumer ───────────────────────────────────
# Allows the hospedajes-sa Kubernetes ServiceAccount to call SQS without
# relying on EC2 IMDS (which is blocked by Istio ambient ztunnel).
resource "aws_iam_role" "hospedajes_sqs" {
  name = "${var.project}-${var.environment}-hospedajes-sqs-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = var.oidc_provider_arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${var.oidc_provider_url}:sub" = "system:serviceaccount:workloads:hospedajes-sa"
          "${var.oidc_provider_url}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "hospedajes_sqs_irsa" {
  role       = aws_iam_role.hospedajes_sqs.name
  policy_arn = aws_iam_policy.sqs_consume_room_availability.arn
}

# ── IRSA Role — reservas_ms SNS publisher ────────────────────────────────────
# Allows the reservas-sa Kubernetes ServiceAccount to publish to SNS without
# relying on EC2 IMDS (which is blocked by Istio ambient ztunnel).
resource "aws_iam_role" "reservas_sns" {
  name = "${var.project}-${var.environment}-reservas-sns-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = var.oidc_provider_arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${var.oidc_provider_url}:sub" = "system:serviceaccount:workloads:reservas-sa"
          "${var.oidc_provider_url}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "reservas_sns_irsa" {
  role       = aws_iam_role.reservas_sns.name
  policy_arn = aws_iam_policy.sns_publish_room_availability.arn
}
