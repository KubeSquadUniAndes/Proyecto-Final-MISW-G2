aws_region      = "us-east-1"
project         = "travelhub"
environment     = "prod"
cluster_version = "1.35"
# db_password is set via TF_VAR_db_password environment variable — never commit this file with a real password
db_password = "SecurePass123!"
