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

openai_api_key   = "REPLACE_ME"
pinecone_api_key = "REPLACE_ME"

pinecone_index_name = "edip-rag-index"
pinecone_namespace  = "edip-phase-6"
openai_embed_model  = "text-embedding-3-small"
openai_chat_model   = "gpt-4.1-mini"

rag_top_k             = 5
rag_max_context_chars = 12000