"use client";

import React, { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  Brain,
  ChevronDown,
  ChevronUp,
  Loader2,
  Send,
  ShieldAlert,
  TrendingUp,
  Workflow,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";

// =========================================================
// Types
// =========================================================
type BusinessAnswer = {
  why?: string | null;
  decision?: string | null;
};

type DecisionSummary = {
  status?: string | null;
  output_type?: string | null;
  final_message?: string | null;
  risk_flags?: string[];
  knowledge_domains?: string[];
};

type ForecastSummary = {
  forecast_units?: number | null;
  forecast_lower_bound?: number | null;
  forecast_upper_bound?: number | null;
  confidence_score?: number | null;
};

type RecommendationSummary = {
  recommended_order_qty?: number | null;
  recommended_transfer_qty?: number | null;
  priority_level?: string | null;
  reason_code?: string | null;
  expected_stockout_risk?: number | null;
  expected_service_level?: number | null;
};

type WorkflowOverview = {
  task_type?: string | null;
  workflow_trace?: string[];
  warnings?: string[];
  rationale_points?: string[];
};

type DebugPayload = {
  request?: Record<string, unknown>;
  raw_summary?: Record<string, unknown>;
};

type WorkflowResponse = {
  question?: string;
  business_answer?: BusinessAnswer;
  decision_summary?: DecisionSummary;
  forecast_summary?: ForecastSummary;
  recommendation_summary?: RecommendationSummary;
  workflow_overview?: WorkflowOverview;
  debug?: DebugPayload;

  // Temporary backward-compatibility keys
  workflow_trace?: string[];
  warnings?: string[];
  [key: string]: unknown;
};

// =========================================================
// Helpers
// =========================================================
const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

function safePercent(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) return "—";
  return `${(value * 100).toFixed(1)}%`;
}

function safeNumber(value?: number | null) {
  if (value === undefined || value === null || Number.isNaN(value)) return "—";
  return value.toLocaleString();
}

function safeText(value?: string | null) {
  if (!value) return "—";
  return value;
}

function statusTone(status?: string | null) {
  const normalized = (status || "").toLowerCase();

  if (normalized.includes("review") || normalized.includes("alert")) {
    return "bg-amber-100 text-amber-800 border-amber-200";
  }

  if (normalized.includes("blocked") || normalized.includes("fail")) {
    return "bg-red-100 text-red-800 border-red-200";
  }

  if (normalized.includes("ready") || normalized.includes("ok")) {
    return "bg-emerald-100 text-emerald-800 border-emerald-200";
  }

  return "bg-slate-100 text-slate-700 border-slate-200";
}

// =========================================================
// Main UI
// =========================================================
export default function EDIPAgentWorkflowUI() {
  const [question, setQuestion] = useState(
    "Why was urgent replenishment recommended for SKU-100245?"
  );
  const [userRole, setUserRole] = useState("");
  const [regionScope, setRegionScope] = useState("");
  const [productId, setProductId] = useState("245");
  const [storeId, setStoreId] = useState("3");
  const [regionId, setRegionId] = useState("1");
  const [warehouseId, setWarehouseId] = useState("");
  const [horizonDays, setHorizonDays] = useState("7");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<WorkflowResponse | null>(null);
  const [showDebug, setShowDebug] = useState(false);

  const payloadPreview = useMemo(
    () => ({
      question,
      user_role: userRole || null,
      region_scope: regionScope || null,
      product_id: productId ? Number(productId) : null,
      store_id: storeId ? Number(storeId) : null,
      warehouse_id: warehouseId ? Number(warehouseId) : null,
      region_id: regionId ? Number(regionId) : null,
      horizon_days: horizonDays ? Number(horizonDays) : 7,
      include_recommendations: true,
      require_approval: false,
      metadata: {
        channel: "react_ui",
        request_origin: "frontend_demo",
      },
    }),
    [
      question,
      userRole,
      regionScope,
      productId,
      storeId,
      warehouseId,
      regionId,
      horizonDays,
    ]
  );

  async function runWorkflow() {
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/agents/workflow/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payloadPreview),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(
          typeof data?.detail === "string"
            ? data.detail
            : "Workflow request failed."
        );
      }

      setResponse(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error.";
      setError(message);
      setResponse(null);
    } finally {
      setLoading(false);
    }
  }

  const businessAnswer = response?.business_answer;
  const decisionSummary = response?.decision_summary;
  const forecastSummary = response?.forecast_summary;
  const recommendationSummary = response?.recommendation_summary;
  const workflowOverview = response?.workflow_overview;
  const debugPayload = response?.debug;

  const workflowTrace =
    workflowOverview?.workflow_trace || response?.workflow_trace || [];
  const warnings = workflowOverview?.warnings || response?.warnings || [];
  const rationalePoints = workflowOverview?.rationale_points || [];
  const riskFlags = decisionSummary?.risk_flags || [];
  const knowledgeDomains = decisionSummary?.knowledge_domains || [];

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-8">
      <div className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-[1.05fr_1.35fr]">
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <Card className="rounded-2xl border-slate-200 shadow-sm">
            <CardHeader>
              <div className="flex items-center justify-between gap-4">
                <div>
                  <CardTitle className="text-2xl font-semibold tracking-tight">
                    EDIP Agent Workflow UI
                  </CardTitle>
                  <p className="mt-2 text-sm text-slate-600">
                    Business-facing React frontend for Planner → Retrieval →
                    Reasoning → Analytics → Execution.
                  </p>
                </div>
                <Badge className="rounded-full px-3 py-1 text-xs">
                  React UI v2
                </Badge>
              </div>
            </CardHeader>

            <CardContent className="space-y-5">
              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">
                  Business Question
                </label>
                <Textarea
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  className="min-h-[120px] rounded-2xl"
                  placeholder="Ask a business decision question..."
                />
              </div>

              <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700">
                    User Role
                  </label>
                  <Input
                    value={userRole}
                    onChange={(e) => setUserRole(e.target.value)}
                    placeholder="planner"
                    className="rounded-2xl"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700">
                    Region Scope
                  </label>
                  <Input
                    value={regionScope}
                    onChange={(e) => setRegionScope(e.target.value)}
                    placeholder="west / enterprise"
                    className="rounded-2xl"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700">
                    Product ID
                  </label>
                  <Input
                    value={productId}
                    onChange={(e) => setProductId(e.target.value)}
                    className="rounded-2xl"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700">
                    Store ID
                  </label>
                  <Input
                    value={storeId}
                    onChange={(e) => setStoreId(e.target.value)}
                    className="rounded-2xl"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700">
                    Warehouse ID
                  </label>
                  <Input
                    value={warehouseId}
                    onChange={(e) => setWarehouseId(e.target.value)}
                    placeholder="optional"
                    className="rounded-2xl"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-slate-700">
                    Region ID
                  </label>
                  <Input
                    value={regionId}
                    onChange={(e) => setRegionId(e.target.value)}
                    className="rounded-2xl"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-slate-700">
                  Forecast Horizon (days)
                </label>
                <Input
                  value={horizonDays}
                  onChange={(e) => setHorizonDays(e.target.value)}
                  className="max-w-[180px] rounded-2xl"
                />
              </div>

              <Button
                onClick={runWorkflow}
                disabled={loading || !question.trim()}
                className="w-full rounded-2xl py-6 text-base"
              >
                {loading ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Send className="mr-2 h-4 w-4" />
                )}
                Run EDIP Workflow
              </Button>

              {error && (
                <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                  {error}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.05 }}
          className="space-y-6"
        >
          <div className="grid gap-4 md:grid-cols-2">
            <Card className="rounded-2xl shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Brain className="h-5 w-5" />
                  Why
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm text-slate-700">
                <p>
                  {safeText(
                    businessAnswer?.why ||
                      "Run the workflow to see the explanation."
                  )}
                </p>

                {rationalePoints.length ? (
                  <ul className="space-y-2">
                    {rationalePoints.map((item, idx) => (
                      <li key={idx} className="rounded-xl bg-slate-50 p-3">
                        • {item}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </CardContent>
            </Card>

            <Card className="rounded-2xl shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Workflow className="h-5 w-5" />
                  Decision
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4 text-sm text-slate-700">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge
                    className={`rounded-full border px-3 py-1 ${statusTone(
                      decisionSummary?.status
                    )}`}
                  >
                    {safeText(decisionSummary?.status)}
                  </Badge>

                  <Badge variant="outline" className="rounded-full">
                    {safeText(decisionSummary?.output_type)}
                  </Badge>
                </div>

                <p>
                  {safeText(
                    businessAnswer?.decision ||
                      decisionSummary?.final_message ||
                      "Run the workflow to see the final decision."
                  )}
                </p>

                {riskFlags.length ? (
                  <div className="space-y-2">
                    <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
                      Risk Flags
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {riskFlags.map((item) => (
                        <Badge
                          key={item}
                          variant="outline"
                          className="rounded-full border-amber-200 bg-amber-50 text-amber-800"
                        >
                          {item}
                        </Badge>
                      ))}
                    </div>
                  </div>
                ) : null}

                <div className="flex flex-wrap gap-2">
                  {workflowTrace.map((step) => (
                    <Badge key={step} variant="outline" className="rounded-full">
                      {step}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            <Card className="rounded-2xl shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <TrendingUp className="h-5 w-5" />
                  Forecast Summary
                </CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-xl bg-slate-50 p-4">
                  <div className="text-slate-500">Forecast Units</div>
                  <div className="mt-1 text-lg font-semibold">
                    {safeNumber(forecastSummary?.forecast_units)}
                  </div>
                </div>

                <div className="rounded-xl bg-slate-50 p-4">
                  <div className="text-slate-500">Confidence</div>
                  <div className="mt-1 text-lg font-semibold">
                    {safePercent(forecastSummary?.confidence_score)}
                  </div>
                </div>

                <div className="rounded-xl bg-slate-50 p-4">
                  <div className="text-slate-500">Lower Bound</div>
                  <div className="mt-1 text-lg font-semibold">
                    {safeNumber(forecastSummary?.forecast_lower_bound)}
                  </div>
                </div>

                <div className="rounded-xl bg-slate-50 p-4">
                  <div className="text-slate-500">Upper Bound</div>
                  <div className="mt-1 text-lg font-semibold">
                    {safeNumber(forecastSummary?.forecast_upper_bound)}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="rounded-2xl shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <ShieldAlert className="h-5 w-5" />
                  Recommendation
                </CardTitle>
              </CardHeader>
              <CardContent className="grid grid-cols-2 gap-3 text-sm">
                <div className="rounded-xl bg-slate-50 p-4">
                  <div className="text-slate-500">Order Qty</div>
                  <div className="mt-1 text-lg font-semibold">
                    {safeNumber(
                      recommendationSummary?.recommended_order_qty
                    )}
                  </div>
                </div>

                <div className="rounded-xl bg-slate-50 p-4">
                  <div className="text-slate-500">Transfer Qty</div>
                  <div className="mt-1 text-lg font-semibold">
                    {safeNumber(
                      recommendationSummary?.recommended_transfer_qty
                    )}
                  </div>
                </div>

                <div className="rounded-xl bg-slate-50 p-4">
                  <div className="text-slate-500">Priority</div>
                  <div className="mt-1 text-lg font-semibold uppercase">
                    {safeText(recommendationSummary?.priority_level)}
                  </div>
                </div>

                <div className="rounded-xl bg-slate-50 p-4">
                  <div className="text-slate-500">Reason Code</div>
                  <div className="mt-1 text-base font-semibold">
                    {safeText(recommendationSummary?.reason_code)}
                  </div>
                </div>

                <div className="rounded-xl bg-slate-50 p-4">
                  <div className="text-slate-500">Stockout Risk</div>
                  <div className="mt-1 text-lg font-semibold">
                    {safePercent(
                      recommendationSummary?.expected_stockout_risk
                    )}
                  </div>
                </div>

                <div className="rounded-xl bg-slate-50 p-4">
                  <div className="text-slate-500">Service Level</div>
                  <div className="mt-1 text-lg font-semibold">
                    {safePercent(
                      recommendationSummary?.expected_service_level
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Card className="rounded-2xl shadow-sm">
            <CardHeader>
              <CardTitle className="text-lg">Workflow Overview</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm text-slate-700">
              <div className="flex flex-wrap gap-2">
                <Badge variant="secondary" className="rounded-full">
                  Task: {safeText(workflowOverview?.task_type)}
                </Badge>

                {knowledgeDomains.map((domain) => (
                  <Badge
                    key={domain}
                    variant="outline"
                    className="rounded-full"
                  >
                    {domain}
                  </Badge>
                ))}
              </div>

              <Separator />

              {warnings.length ? (
                <div className="space-y-2 rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-800">
                  <div className="flex items-center gap-2 font-medium">
                    <AlertTriangle className="h-4 w-4" />
                    Warnings
                  </div>
                  <ul className="space-y-1">
                    {warnings.map((item, idx) => (
                      <li key={idx}>• {item}</li>
                    ))}
                  </ul>
                </div>
              ) : (
                <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-emerald-800">
                  No warnings.
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="rounded-2xl shadow-sm">
            <CardHeader>
              <button
                type="button"
                onClick={() => setShowDebug((prev) => !prev)}
                className="flex w-full items-center justify-between text-left"
              >
                <CardTitle className="text-lg">Debug Payload</CardTitle>
                {showDebug ? (
                  <ChevronUp className="h-5 w-5" />
                ) : (
                  <ChevronDown className="h-5 w-5" />
                )}
              </button>
            </CardHeader>

            {showDebug && (
              <CardContent className="space-y-4">
                <div>
                  <div className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">
                    Request
                  </div>
                  <pre className="overflow-x-auto rounded-2xl bg-slate-950 p-4 text-xs text-slate-100">
                    {JSON.stringify(debugPayload?.request || payloadPreview, null, 2)}
                  </pre>
                </div>

                <div>
                  <div className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-500">
                    Raw Summary
                  </div>
                  <pre className="overflow-x-auto rounded-2xl bg-slate-950 p-4 text-xs text-slate-100">
                    {JSON.stringify(debugPayload?.raw_summary || response, null, 2)}
                  </pre>
                </div>
              </CardContent>
            )}
          </Card>
        </motion.div>
      </div>
    </div>
  );
}