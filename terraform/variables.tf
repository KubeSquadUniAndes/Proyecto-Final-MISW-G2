 variable "cluster_name" {
  description = "istio-eks"
  type        = string
  default     = "istio-eks"
}

variable "aws_profile" {
  description = "AWS CLI profile name used by Terraform provider"
  type        = string
  default     = ""
}

variable "region" {
  type    = string
  default = "us-west-2"
}