aws_region      = "us-east-1"
project         = "travelhub"
environment     = "prod"
cluster_version = "1.35"
# All secrets (db_password, jwt_secret, aes_key) are managed by AWS Secrets Manager.
# See terraform/envs/prod/main.tf for the required secret names.
