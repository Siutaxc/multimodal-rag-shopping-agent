"use client";

import Link from "next/link";

import type { AssistantResponse, SearchResponse } from "../product-types";

export function AgentTraceSummary({ response }: { response: AssistantResponse }) {
  return (
    <details className="trace-panel">
      <summary>
        <span>开发者轨迹</span>
        <span>{response.trace.tool_steps.length}/4 工具步骤 · {response.trace.total_latency_ms.toFixed(2)} ms</span>
      </summary>
      {response.trace.degraded_reasons.length ? (
        <p className="trace-warning" role="status">
          部分降级：{response.trace.degraded_reasons.join("、")}
        </p>
      ) : null}
      <div className="trace-grid">
        <div>
          <strong>有界状态机</strong>
          {response.trace.states.map((state, index) => <span key={`${state}-${index}`}>{index + 1}. {state}</span>)}
        </div>
        <div>
          <strong>白名单工具</strong>
          {response.trace.tool_steps.map((step) => (
            <span key={step.step}>{step.step}. {step.tool} · {step.status} · {step.latency_ms.toFixed(2)} ms</span>
          ))}
        </div>
        <div>
          <strong>引用校验</strong>
          <span>{response.trace.citation_validation.valid ? "通过" : "已安全回退"}</span>
          <span>检查 {response.trace.citation_validation.checked_statement_count} 条陈述</span>
          <Link href={`/traces/${response.trace_id}`}>打开完整轨迹 →</Link>
        </div>
      </div>
    </details>
  );
}

export function SearchTraceSummary({ response }: { response: SearchResponse }) {
  const textTrace = response.trace.text_trace;
  const lexicalCount = response.trace.channels.lexical?.length ?? textTrace?.channels.lexical?.length ?? 0;
  const denseCount = response.trace.channels.dense?.length ?? textTrace?.channels.dense?.length ?? 0;
  const fusionCount = response.trace.fusion?.length ?? textTrace?.fusion.length ?? 0;
  const rerankCount = response.trace.rerank?.length ?? textTrace?.rerank.length ?? 0;
  return (
    <details className="trace-panel">
      <summary>
        <span>检索轨迹 · {response.retrieval_mode}</span>
        <span>{response.trace.latency_ms.total?.toFixed(2) ?? "—"} ms</span>
      </summary>
      {response.trace.degraded_reason ? (
        <p className="trace-warning" role="status">部分降级：{response.trace.degraded_reason}</p>
      ) : null}
      <div className="trace-grid">
        <div>
          <strong>模型身份</strong>
          {Object.entries(response.trace.models).map(([name, value]) => <span key={name}>{name}: {value}</span>)}
        </div>
        <div>
          <strong>通道候选</strong>
          <span>词法：{lexicalCount}</span>
          <span>文本向量：{denseCount}</span>
          <span>图片向量：{response.trace.channels.image?.length ?? 0}</span>
          <span>融合：{fusionCount}</span>
          <span>重排：{rerankCount}</span>
        </div>
        <div>
          <strong>阶段耗时</strong>
          {Object.entries(response.trace.latency_ms).map(([name, value]) => <span key={name}>{name}: {value.toFixed(2)} ms</span>)}
        </div>
      </div>
    </details>
  );
}
