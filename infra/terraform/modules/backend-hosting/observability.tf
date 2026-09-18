resource "aws_cloudwatch_dashboard" "backend" {
  dashboard_name = "${local.name}-operations"
  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "ECS resource utilization"
          view    = "timeSeries"
          region  = var.region
          period  = 300
          stacked = false
          metrics = [
            ["AWS/ECS", "CPUUtilization", "ClusterName", aws_ecs_cluster.backend.name, "ServiceName", aws_ecs_service.backend.name, { label = "CPU utilization", stat = "Average" }],
            ["AWS/ECS", "MemoryUtilization", "ClusterName", aws_ecs_cluster.backend.name, "ServiceName", aws_ecs_service.backend.name, { label = "Memory utilization", stat = "Average" }],
          ]
          yAxis = {
            left = { min = 0, max = 100, label = "Percent" }
          }
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "ALB traffic and target latency"
          view    = "timeSeries"
          region  = var.region
          period  = 300
          stacked = false
          metrics = [
            ["AWS/ApplicationELB", "RequestCount", "LoadBalancer", aws_lb.backend.arn_suffix, { label = "Requests", stat = "Sum", yAxis = "left" }],
            ["AWS/ApplicationELB", "TargetResponseTime", "LoadBalancer", aws_lb.backend.arn_suffix, { label = "Target response time", stat = "Average", yAxis = "right" }],
          ]
          yAxis = {
            left  = { min = 0, label = "Requests" }
            right = { min = 0, label = "Seconds" }
          }
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "ALB HTTP 5xx errors"
          view    = "timeSeries"
          region  = var.region
          period  = 300
          stacked = false
          metrics = [
            ["AWS/ApplicationELB", "HTTPCode_ELB_5XX_Count", "LoadBalancer", aws_lb.backend.arn_suffix, { label = "ALB 5xx", stat = "Sum" }],
            ["AWS/ApplicationELB", "HTTPCode_Target_5XX_Count", "LoadBalancer", aws_lb.backend.arn_suffix, "TargetGroup", aws_lb_target_group.backend.arn_suffix, { label = "Target 5xx", stat = "Sum" }],
          ]
          yAxis = {
            left = { min = 0, label = "Errors" }
          }
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "ALB target health"
          view    = "timeSeries"
          region  = var.region
          period  = 60
          stacked = false
          metrics = [
            ["AWS/ApplicationELB", "HealthyHostCount", "LoadBalancer", aws_lb.backend.arn_suffix, "TargetGroup", aws_lb_target_group.backend.arn_suffix, { label = "Healthy targets", stat = "Minimum" }],
            ["AWS/ApplicationELB", "UnHealthyHostCount", "LoadBalancer", aws_lb.backend.arn_suffix, "TargetGroup", aws_lb_target_group.backend.arn_suffix, { label = "Unhealthy targets", stat = "Maximum" }],
          ]
          yAxis = {
            left = { min = 0, label = "Targets" }
          }
        }
      },
    ]
  })
}

resource "aws_cloudwatch_metric_alarm" "unhealthy_target" {
  alarm_name          = "${local.name}-unhealthy-target"
  alarm_description   = "At least one ALB target was unhealthy for two consecutive minutes."
  namespace           = "AWS/ApplicationELB"
  metric_name         = "UnHealthyHostCount"
  dimensions          = { LoadBalancer = aws_lb.backend.arn_suffix, TargetGroup = aws_lb_target_group.backend.arn_suffix }
  statistic           = "Maximum"
  period              = 60
  evaluation_periods  = 2
  datapoints_to_alarm = 2
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = []
  ok_actions          = []
}

resource "aws_cloudwatch_metric_alarm" "high_cpu" {
  alarm_name          = "${local.name}-high-cpu"
  alarm_description   = "Average ECS CPU utilization was at least 80% for 15 minutes."
  namespace           = "AWS/ECS"
  metric_name         = "CPUUtilization"
  dimensions          = { ClusterName = aws_ecs_cluster.backend.name, ServiceName = aws_ecs_service.backend.name }
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 3
  datapoints_to_alarm = 3
  threshold           = 80
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = []
  ok_actions          = []
}

resource "aws_cloudwatch_metric_alarm" "high_memory" {
  alarm_name          = "${local.name}-high-memory"
  alarm_description   = "Average ECS memory utilization was at least 80% for 15 minutes."
  namespace           = "AWS/ECS"
  metric_name         = "MemoryUtilization"
  dimensions          = { ClusterName = aws_ecs_cluster.backend.name, ServiceName = aws_ecs_service.backend.name }
  statistic           = "Average"
  period              = 300
  evaluation_periods  = 3
  datapoints_to_alarm = 3
  threshold           = 80
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = []
  ok_actions          = []
}
