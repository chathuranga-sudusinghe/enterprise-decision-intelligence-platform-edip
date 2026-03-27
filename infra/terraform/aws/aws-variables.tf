# =========================================================
# Core project variables
# =========================================================
variable "project_name" {
  description = "Project name prefix used for AWS resources."
  type        = string
  default     = "edip"
}

variable "environment" {
  description = "Deployment environment name."
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for deployment."
  type        = string
  default     = "ap-south-1"
}

# =========================================================
# Network variables
# =========================================================
variable "vpc_cidr" {
  description = "CIDR block for the main VPC."
  type        = string
  default     = "10.10.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets."
  type        = list(string)
  default = [
    "10.10.1.0/24",
    "10.10.2.0/24"
  ]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets."
  type        = list(string)
  default = [
    "10.10.11.0/24",
    "10.10.12.0/24"
  ]
}

variable "availability_zones" {
  description = "Availability zones used by the VPC."
  type        = list(string)
  default = [
    "ap-south-1a",
    "ap-south-1b"
  ]
}

# =========================================================
# App / container variables
# =========================================================
variable "container_port" {
  description = "Application container port."
  type        = number
  default     = 8000
}

variable "health_check_path" {
  description = "ALB health check path."
  type        = string
  default     = "/health"
}

variable "ecs_task_cpu" {
  description = "CPU units for ECS task."
  type        = number
  default     = 512
}

variable "ecs_task_memory" {
  description = "Memory (MiB) for ECS task."
  type        = number
  default     = 1024
}

variable "desired_count" {
  description = "Desired ECS service task count."
  type        = number
  default     = 1
}

variable "app_image_tag" {
  description = "Docker image tag pushed to ECR."
  type        = string
  default     = "latest"
}

# =========================================================
# Environment variables for EDIP API
# =========================================================
variable "app_name" {
  description = "FastAPI application name."
  type        = string
  default     = "EDIP API"
}

variable "app_version" {
  description = "FastAPI application version."
  type        = string
  default     = "1.0.0"
}

variable "app_env" {
  description = "Application environment."
  type        = string
  default     = "production"
}

variable "api_host" {
  description = "API bind host."
  type        = string
  default     = "0.0.0.0"
}

variable "api_port" {
  description = "API bind port."
  type        = number
  default     = 8000
}

variable "allow_credentials" {
  description = "CORS allow credentials flag."
  type        = bool
  default     = true
}

variable "allowed_origins" {
  description = "Comma-separated CORS origins string for the app."
  type        = string
  default     = "*"
}

variable "openai_api_key" {
  description = "OpenAI API key."
  type        = string
  sensitive   = true
}

variable "pinecone_api_key" {
  description = "Pinecone API key."
  type        = string
  sensitive   = true
}

variable "pinecone_index_name" {
  description = "Pinecone index name."
  type        = string
  default     = "edip-rag-index"
}

variable "pinecone_namespace" {
  description = "Pinecone namespace."
  type        = string
  default     = "edip-phase-6"
}

variable "openai_embed_model" {
  description = "Embedding model name."
  type        = string
  default     = "text-embedding-3-small"
}

variable "openai_chat_model" {
  description = "Chat model name."
  type        = string
  default     = "gpt-4.1-mini"
}

variable "rag_top_k" {
  description = "Top-k retrieval count."
  type        = number
  default     = 5
}

variable "rag_max_context_chars" {
  description = "Maximum RAG context length."
  type        = number
  default     = 12000
}