 output "sns_topic_arn" {
  description = "ARN of the SNS topic that receives room availability events from reservas_ms"
  value       = aws_sns_topic.room_availability.arn
}

output "sns_topic_name" {
  description = "Name of the SNS room availability topic"
  value       = aws_sns_topic.room_availability.name
}

output "sqs_queue_url" {
  description = "URL of the SQS queue consumed by hospedajes_ms (set as SQS_QUEUE_URL env var)"
  value       = aws_sqs_queue.hospedajes_availability.id
}

output "sqs_queue_arn" {
  description = "ARN of the SQS room availability queue"
  value       = aws_sqs_queue.hospedajes_availability.arn
}

output "sqs_dlq_url" {
  description = "URL of the dead-letter queue for messages that failed processing after max_receive_count attempts"
  value       = aws_sqs_queue.hospedajes_availability_dlq.id
}

output "sqs_dlq_arn" {
  description = "ARN of the dead-letter queue"
  value       = aws_sqs_queue.hospedajes_availability_dlq.arn
}
