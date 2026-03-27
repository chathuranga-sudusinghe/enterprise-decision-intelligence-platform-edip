resource "kubernetes_config_map" "prometheus_config" {
  metadata {
    name      = "prometheus-config"
    namespace = kubernetes_namespace.edip.metadata[0].name
  }

  data = {
    "prometheus.yml" = <<-EOT
      global:
        scrape_interval: 15s
        evaluation_interval: 15s

      scrape_configs:
        - job_name: "edip_api"
          metrics_path: /metrics
          static_configs:
            - targets:
                - "edip-api:8000"
    EOT
  }

  depends_on = [kubernetes_namespace.edip]
}

resource "kubernetes_deployment" "prometheus" {
  metadata {
    name      = var.prometheus_name
    namespace = kubernetes_namespace.edip.metadata[0].name

    labels = {
      app = var.prometheus_name
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = var.prometheus_name
      }
    }

    template {
      metadata {
        labels = {
          app = var.prometheus_name
        }
      }

      spec {
        container {
          name  = var.prometheus_name
          image = "prom/prometheus:latest"

          port {
            container_port = var.prometheus_port
          }

          args = [
            "--config.file=/etc/prometheus/prometheus.yml"
          ]

          volume_mount {
            name       = "prometheus-config-volume"
            mount_path = "/etc/prometheus"
          }

          resources {
            requests = {
              cpu    = "100m"
              memory = "128Mi"
            }

            limits = {
              cpu    = "300m"
              memory = "256Mi"
            }
          }
        }

        volume {
          name = "prometheus-config-volume"

          config_map {
            name = kubernetes_config_map.prometheus_config.metadata[0].name
          }
        }
      }
    }
  }

  depends_on = [
    kubernetes_namespace.edip,
    kubernetes_config_map.prometheus_config
  ]
}

resource "kubernetes_service" "prometheus" {
  metadata {
    name      = var.prometheus_name
    namespace = kubernetes_namespace.edip.metadata[0].name
  }

  spec {
    selector = {
      app = var.prometheus_name
    }

    port {
      name        = "http"
      port        = var.prometheus_port
      target_port = var.prometheus_port
    }

    type = "ClusterIP"
  }

  depends_on = [kubernetes_deployment.prometheus]
}