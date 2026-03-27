variable "kubeconfig_path" {
  description = "Path to the kubeconfig file used to connect to Kubernetes."
  type        = string
}

variable "namespace" {
  description = "Kubernetes namespace for EDIP resources."
  type        = string
  default     = "edip"
}

variable "api_name" {
  description = "API application name."
  type        = string
  default     = "edip-api"
}

variable "api_image" {
  description = "Docker image for the EDIP API."
  type        = string
}

variable "api_port" {
  description = "Container and service port for the API."
  type        = number
  default     = 8000
}

variable "prometheus_name" {
  description = "Prometheus deployment/service name."
  type        = string
  default     = "prometheus"
}

variable "prometheus_port" {
  description = "Prometheus container and service port."
  type        = number
  default     = 9090
}

variable "grafana_name" {
  description = "Grafana deployment/service name."
  type        = string
  default     = "grafana"
}

variable "grafana_port" {
  description = "Grafana container and service port."
  type        = number
  default     = 3000
}

variable "grafana_admin_user" {
  description = "Grafana admin username."
  type        = string
  default     = "admin"
}

variable "grafana_admin_password" {
  description = "Grafana admin password."
  type        = string
  sensitive   = true
  default     = "admin"
}