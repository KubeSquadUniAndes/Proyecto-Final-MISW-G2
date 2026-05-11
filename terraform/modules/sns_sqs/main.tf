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
