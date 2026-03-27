resource "kubernetes_config_map" "grafana_datasource_config" {
  metadata {
    name      = "grafana-datasource-config"
    namespace = kubernetes_namespace.edip.metadata[0].name
  }

  data = {
    "datasource.yml" = <<-EOT
      apiVersion: 1
      datasources:
        - name: Prometheus
          type: prometheus
          uid: prometheus
          access: proxy
          url: http://prometheus:9090
          isDefault: true
          editable: true
    EOT
  }

  depends_on = [kubernetes_namespace.edip]
}

resource "kubernetes_config_map" "grafana_dashboard_provisioning_config" {
  metadata {
    name      = "grafana-dashboard-provisioning-config"
    namespace = kubernetes_namespace.edip.metadata[0].name
  }

  data = {
    "dashboard.yml" = <<-EOT
      apiVersion: 1

      providers:
        - name: "EDIP Dashboards"
          orgId: 1
          folder: "EDIP"
          type: file
          disableDeletion: false
          updateIntervalSeconds: 10
          allowUiUpdates: true
          options:
            path: /var/lib/grafana/dashboards
    EOT
  }

  depends_on = [kubernetes_namespace.edip]
}

resource "kubernetes_config_map" "grafana_alerting_config" {
  metadata {
    name      = "grafana-alerting-config"
    namespace = kubernetes_namespace.edip.metadata[0].name
  }

  data = {
    "edip-alert-rules.yml" = <<-EOT
      apiVersion: 1

      groups:
        - orgId: 1
          name: EDIP Alert Rules
          folder: EDIP
          interval: 1m
          rules:
            - uid: edip_api_down
              title: EDIP API Down
              condition: A
              data:
                - refId: A
                  relativeTimeRange:
                    from: 300
                    to: 0
                  datasourceUid: prometheus
                  model:
                    editorMode: code
                    expr: up{job="edip_api"} == 0
                    instant: true
                    intervalMs: 1000
                    maxDataPoints: 43200
                    refId: A
              noDataState: OK
              execErrState: Alerting
              for: 2m
              annotations:
                summary: EDIP API is down.
                description: Prometheus could not confirm the edip_api target is up for 2 minutes.
              labels:
                severity: critical
                service: edip-api

            - uid: edip_workflow_errors_high
              title: EDIP Workflow Errors Increasing
              condition: A
              data:
                - refId: A
                  relativeTimeRange:
                    from: 300
                    to: 0
                  datasourceUid: prometheus
                  model:
                    editorMode: code
                    expr: sum(increase(edip_workflow_run_errors_total[5m])) > 0
                    instant: true
                    intervalMs: 1000
                    maxDataPoints: 43200
                    refId: A
              noDataState: OK
              execErrState: Alerting
              for: 1m
              annotations:
                summary: EDIP workflow errors detected.
                description: One or more workflow errors were recorded in the last 5 minutes.
              labels:
                severity: warning
                service: edip-workflow
    EOT
  }

  depends_on = [kubernetes_namespace.edip]
}

resource "kubernetes_config_map" "grafana_dashboard_json_config" {
  metadata {
    name      = "grafana-dashboard-json-config"
    namespace = kubernetes_namespace.edip.metadata[0].name
  }

  data = {
    "edip-overview.json" = <<-EOT
{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": {
          "type": "grafana",
          "uid": "-- Grafana --"
        },
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "fiscalYearStartMonth": 0,
  "graphTooltip": 0,
  "id": null,
  "links": [],
  "liveNow": false,
  "panels": [
    {
      "type": "stat",
      "title": "EDIP API Up",
      "gridPos": { "h": 4, "w": 4, "x": 0, "y": 0 },
      "datasource": { "type": "prometheus", "uid": "prometheus" },
      "targets": [
        {
          "expr": "up{job=\"edip_api\"}",
          "refId": "A"
        }
      ]
    }
  ],
  "refresh": "10s",
  "schemaVersion": 39,
  "style": "dark",
  "tags": ["edip", "monitoring"],
  "templating": { "list": [] },
  "time": { "from": "now-15m", "to": "now" },
  "timepicker": {},
  "timezone": "browser",
  "title": "EDIP Overview",
  "version": 1,
  "weekStart": ""
}
    EOT
  }

  depends_on = [kubernetes_namespace.edip]
}

resource "kubernetes_deployment" "grafana" {
  metadata {
    name      = var.grafana_name
    namespace = kubernetes_namespace.edip.metadata[0].name

    labels = {
      app = var.grafana_name
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = var.grafana_name
      }
    }

    template {
      metadata {
        labels = {
          app = var.grafana_name
        }
      }

      spec {
        container {
          name  = var.grafana_name
          image = "grafana/grafana:latest"

          port {
            container_port = var.grafana_port
          }

          env {
            name  = "GF_SECURITY_ADMIN_USER"
            value = var.grafana_admin_user
          }

          env {
            name  = "GF_SECURITY_ADMIN_PASSWORD"
            value = var.grafana_admin_password
          }

          volume_mount {
            name       = "grafana-datasource-volume"
            mount_path = "/etc/grafana/provisioning/datasources"
          }

          volume_mount {
            name       = "grafana-dashboard-provisioning-volume"
            mount_path = "/etc/grafana/provisioning/dashboards"
          }

          volume_mount {
            name       = "grafana-alerting-volume"
            mount_path = "/etc/grafana/provisioning/alerting"
          }

          volume_mount {
            name       = "grafana-dashboard-json-volume"
            mount_path = "/var/lib/grafana/dashboards"
          }

          resources {
            requests = {
              cpu    = "100m"
              memory = "192Mi"
            }

            limits = {
              cpu    = "300m"
              memory = "384Mi"
            }
          }
        }

        volume {
          name = "grafana-datasource-volume"

          config_map {
            name = kubernetes_config_map.grafana_datasource_config.metadata[0].name
          }
        }

        volume {
          name = "grafana-dashboard-provisioning-volume"

          config_map {
            name = kubernetes_config_map.grafana_dashboard_provisioning_config.metadata[0].name
          }
        }

        volume {
          name = "grafana-alerting-volume"

          config_map {
            name = kubernetes_config_map.grafana_alerting_config.metadata[0].name
          }
        }

        volume {
          name = "grafana-dashboard-json-volume"

          config_map {
            name = kubernetes_config_map.grafana_dashboard_json_config.metadata[0].name
          }
        }
      }
    }
  }

  depends_on = [
    kubernetes_namespace.edip,
    kubernetes_config_map.grafana_datasource_config,
    kubernetes_config_map.grafana_dashboard_provisioning_config,
    kubernetes_config_map.grafana_alerting_config,
    kubernetes_config_map.grafana_dashboard_json_config
  ]
}

resource "kubernetes_service" "grafana" {
  metadata {
    name      = var.grafana_name
    namespace = kubernetes_namespace.edip.metadata[0].name
  }

  spec {
    selector = {
      app = var.grafana_name
    }

    port {
      name        = "http"
      port        = var.grafana_port
      target_port = var.grafana_port
    }

    type = "NodePort"
  }

  depends_on = [kubernetes_deployment.grafana]
}