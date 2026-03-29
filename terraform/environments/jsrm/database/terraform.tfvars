aws_region               = "us-east-1"
db_publicly_accessible   = true # para pruebas, no recomendado en producción
sg_ingress_cidr_blocks   = ["0.0.0.0/0"] # para pruebas, no recomendado en producción
secret_name              = "terraform-travelHub/db-credentials"
db_allocated_storage_gib = 20 # Almacenamiento inicial en GB https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Storage.html
db_name                  = "travelhubdb"
owner                    = "js.rodriguezm" # Reemplazar con el nombre de usuario real