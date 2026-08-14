project_name = "edip"
environment  = "dev"
aws_region   = "ap-south-1"

app_image_tag = "latest"
desired_count = 1

app_name    = "EDIP API"
app_version = "1.0.0"
app_env     = "production"

api_host = "0.0.0.0"
api_port = 8000

allowed_origins   = "*"
allow_credentials = true
