resource "kubernetes_namespace" "edip" {
  metadata {
    name = var.namespace
  }
}