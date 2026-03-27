output "namespace_name" {
  description = "EDIP Kubernetes namespace name."
  value       = kubernetes_namespace.edip.metadata[0].name
}

output "api_service_name" {
  description = "EDIP API service name."
  value       = kubernetes_service.api.metadata[0].name
}

output "prometheus_service_name" {
  description = "Prometheus service name."
  value       = kubernetes_service.prometheus.metadata[0].name
}

output "grafana_service_name" {
  description = "Grafana service name."
  value       = kubernetes_service.grafana.metadata[0].name
}