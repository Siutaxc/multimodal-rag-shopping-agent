"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import SiteHeader from "../../components/SiteHeader";
import { apiBaseUrl, type AgentTraceDetail } from "../../product-types";
import { ApiRequestError, requestJson } from "../../shoplens-client";

export default function TraceView({ traceId }: { traceId: string }) {
  const [trace, setTrace] = useState<AgentTraceDetail | null>(null);
  const [status, setStatus] = useState("正在读取开发轨迹…");
  const [failed, setFailed] = useState(false);

  const load = useCallback(async () => {
    setFailed(false);
    setStatus("正在读取开发轨迹…");
    try {
      const payload = await requestJson<AgentTraceDetail>(`${apiBaseUrl()}/api/v1/traces/${traceId}`);
      setTrace(payload);
      setStatus("轨迹已加载。会话标识未在页面中展示。");
    } catch (error) {
      setFailed(true);
      setStatus(error instanceof ApiRequestError && error.status === 404 ? "轨迹不存在，已过期，或生产环境已关闭轨迹读取。" : `轨迹读取失败：${error instanceof Error ? error.message : "未知错误"}`);
    }
  }, [traceId]);

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  return (
    <main className="workspace-shell trace-shell" id="main-content">
      <SiteHeader compact />
      <section className="results-top" aria-labelledby="trace-title">
        <div><p className="eyebrow">DEVELOPMENT ONLY · BOUNDED TRACE</p><h1 id="trace-title">Query Trace</h1><p className="lede">展示解析、确定性硬过滤、白名单工具和引用校验；不公开会话标识。</p></div>
        {trace ? <div className="result-count"><strong>{trace.tool_steps.length}/4</strong><span>TOOLS</span></div> : null}
      </section>
      <div className={`system-notice${failed ? " system-notice-error" : ""}`}><p role={failed ? "alert" : "status"}>{status}</p>{failed ? <button onClick={load} type="button">重新读取</button> : null}</div>

      {trace ? (
        <div className="trace-detail-grid">
          <section><span className="trace-index">01</span><h2>状态机</h2><ol>{trace.states.map((state) => <li key={state}>{state}</li>)}</ol></section>
          <section><span className="trace-index">02</span><h2>生效硬条件</h2><KeyValueList value={trace.effective_filters} /></section>
          <section><span className="trace-index">03</span><h2>引用校验</h2><p className="trace-verdict">{trace.citation_validation.valid ? "VALID" : "SAFE FALLBACK"}</p><p>检查 {trace.citation_validation.checked_statement_count} 条结构化陈述。</p>{trace.citation_validation.errors.map((error) => <code key={error}>{error}</code>)}</section>
          <section className="trace-tools"><span className="trace-index">04</span><h2>白名单工具步骤</h2>{trace.tool_steps.map((step) => <article key={step.step}><header><strong>{step.step}. {step.tool}</strong><span>{step.status} · {step.latency_ms.toFixed(2)} ms</span></header><div><div><h3>输入</h3><pre>{JSON.stringify(step.input, null, 2)}</pre></div><div><h3>输出摘要</h3><pre>{JSON.stringify(step.output, null, 2)}</pre></div></div></article>)}</section>
          <section><span className="trace-index">05</span><h2>模型调用</h2>{trace.model_calls.length ? <ul>{trace.model_calls.map((call, index) => <li key={`${call.phase}-${index}`}>{call.phase} · {call.model} · {call.status} · {call.latency_ms.toFixed(2)} ms</li>)}</ul> : <p>本轮未调用外部模型。</p>}</section>
          <section><span className="trace-index">06</span><h2>降级与耗时</h2><p>{trace.degraded_reasons.length ? trace.degraded_reasons.join("、") : "无降级"}</p><strong className="trace-total">{trace.total_latency_ms.toFixed(2)} ms</strong></section>
        </div>
      ) : null}
      <div className="trace-back"><Link className="primary-button" href="/results">← 返回当前结果</Link></div>
    </main>
  );
}

function KeyValueList({ value }: { value: Record<string, string | boolean | null> }) {
  const entries = Object.entries(value).filter(([, item]) => item != null);
  if (!entries.length) return <p>未设置硬条件。</p>;
  return <dl className="key-value-list">{entries.map(([key, item]) => <div key={key}><dt>{key}</dt><dd>{String(item)}</dd></div>)}</dl>;
}
