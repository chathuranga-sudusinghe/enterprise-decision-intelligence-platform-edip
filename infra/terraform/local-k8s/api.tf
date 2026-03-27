resource "kubernetes_deployment" "api" {
  metadata {
    name      = var.api_name
    namespace = kubernetes_namespace.edip.metadata[0].name

    labels = {
      app = var.api_name
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = var.api_name
      }
    }

    template {
      metadata {
        labels = {
          app = var.api_name
        }
      }

      spec {
        container {
          name              = var.api_name
          image             = var.api_image
          image_pull_policy = "IfNotPresent"

          port {
            container_port = var.api_port
          }

          env {
            name  = "PYTHONUNBUFFERED"
            value = "1"
          }

          resources {
            requests = {
              cpu    = "250m"
              memory = "256Mi"
            }

            limits = {
              cpu    = "500m"
              memory = "512Mi"
            }
          }

          readiness_probe {
            http_get {
              path = "/metrics"
              port = var.api_port
            }

            initial_delay_seconds = 10
            period_seconds        = 15
          }

          liveness_probe {
            http_get {
              path = "/metrics"
              port = var.api_port
            }

            initial_delay_seconds = 20
            period_seconds        = 20
          }
        }
      }
    }
  }

  depends_on = [kubernetes_namespace.edip]
}

resource "kubernetes_service" "api" {
  metadata {
    name      = var.api_name
    namespace = kubernetes_namespace.edip.metadata[0].name
  }

  spec {
    selector = {
      app = var.api_name
    }

    port {
      name        = "http"
      port        = var.api_port
      target_port = var.api_port
    }

    type = "ClusterIP"
  }

  depends_on = [kubernetes_deployment.api]
}