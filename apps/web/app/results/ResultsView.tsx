"use client";

import type { MouseEvent } from "react";
import { useEffect, useMemo, useRef, useState } from "react";

import ComparisonTray from "../components/ComparisonTray";
import { AgentProductGrid, SearchProductGrid } from "../components/ProductCards";
import SearchComposer from "../components/SearchComposer";
import SiteHeader from "../components/SiteHeader";
import { AgentTraceSummary, SearchTraceSummary } from "../components/TraceSummary";
import type {
  FilterField,
  ProductSummary,
  SearchDraft,
  SessionContext,
} from "../product-types";
import {
  ApiRequestError,
  DEFAULT_DRAFT,
  executeSearch,
  readComparison,
  readLocalValue,
  removeLocalValue,
  requestJson,
  saveSearchExecution,
  type SearchSnapshot,
  STORAGE_KEYS,
  writeComparison,
} from "../shoplens-client";
import { apiBaseUrl } from "../product-types";

const filterLabels: Record<string, string> = {
  category: "类型",
  brand: "品牌",
  price_min: "最低价格",
  price_max: "最高价格",
  currency: "币种",
  wireless: "无线",
  anc: "主动降噪",
  battery_hours_min: "最低续航",
  weight_grams_max: "最高重量",
  color: "颜色",
  codec: "编码",
  water_resistance: "防水",
};

export default function ResultsView() {
  const [snapshot, setSnapshot] = useState<SearchSnapshot | null>(null);
  const [comparison, setComparison] = useState<ProductSummary[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const [notice, setNotice] = useState("正在恢复当前设备上的最近结果…");
  const [failure, setFailure] = useState<ApiRequestError | null>(null);
  const resultHeading = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const restored = readLocalValue<SearchSnapshot>(STORAGE_KEYS.snapshot);
      const restoredSessionId = readLocalValue<string>(STORAGE_KEYS.session);
      setSnapshot(restored);
      setSessionId(restoredSessionId);
      setComparison(readComparison());
      setHydrated(true);
      setNotice(restored ? restoredNotice(restored) : "还没有结果，提交一次导购需求即可开始。");

      if (restoredSessionId) {
        requestJson<SessionContext>(`${apiBaseUrl()}/api/v1/sessions/${restoredSessionId}`)
          .then((context) => {
            setNotice(`会话已恢复，条件更新于 ${new Date(context.updated_at).toLocaleString("zh-CN")}。`);
          })
          .catch((error: unknown) => {
            if (error instanceof ApiRequestError && error.status === 404) {
              removeLocalValue(STORAGE_KEYS.session);
              setSessionId(null);
              setNotice("上次会话已失效；已有结果仍可查看，下次提交会创建新会话。");
            } else {
              setNotice("会话状态暂不可读取；已有结果仍可查看，提交时会尝试恢复。");
            }
          });
      }
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const selectedIds = useMemo(() => new Set(comparison.map((item) => item.id)), [comparison]);
  const total = snapshot?.agentResults?.recommendations.length ?? snapshot?.results?.items.length ?? 0;

  async function runSearch(draft: SearchDraft, image: File | null, clearFields: FilterField[] = []) {
    setBusy(true);
    setFailure(null);
    setNotice(image ? "正在安全处理图片并检索…" : "正在检索并核验证据…");
    try {
      const execution = await executeSearch({ draft, image, sessionId, clearFields });
      const next = saveSearchExecution(draft, execution);
      setSnapshot(next);
      if (execution.agentResults) setSessionId(execution.agentResults.session_id);
      const degraded = execution.agentResults?.trace.degraded_reasons.length || execution.results?.trace.degraded_reason;
      setNotice(degraded ? "结果已返回，但部分能力发生降级，详情见开发者轨迹。" : `已返回 ${execution.agentResults?.recommendations.length ?? execution.results?.items.length ?? 0} 件商品。`);
      window.setTimeout(() => resultHeading.current?.focus(), 0);
    } catch (error) {
      const requestError = error instanceof ApiRequestError ? error : new ApiRequestError("未知错误");
      setFailure(requestError);
      setNotice(requestError.kind === "timeout" ? requestError.message : `请求失败：${requestError.message}`);
    } finally {
      setBusy(false);
    }
  }

  function toggleComparison(product: ProductSummary) {
    const exists = comparison.some((item) => item.id === product.id);
    const next = exists ? comparison.filter((item) => item.id !== product.id) : [...comparison, product].slice(0, 4);
    setComparison(next);
    writeComparison(next);
  }

  function removeComparison(productId: string) {
    const next = comparison.filter((item) => item.id !== productId);
    setComparison(next);
    writeComparison(next);
  }

  async function clearFilter(event: MouseEvent<HTMLButtonElement>, field: FilterField) {
    event.preventDefault();
    if (!snapshot) return;
    const draft = clearDraftField(snapshot.draft, field);
    await runSearch(draft, null, snapshot.agentResults ? [field] : []);
  }

  async function recoverEmpty() {
    if (!snapshot) return;
    const fields = Object.entries(snapshot.agentResults?.applied_filters ?? {})
      .filter(([, value]) => value != null)
      .map(([field]) => field as FilterField);
    const draft = { ...snapshot.draft, category: "", priceMax: "", anc: "" as const };
    await runSearch(draft, null, snapshot.agentResults ? fields : []);
  }

  const appliedFilters = snapshot?.agentResults?.applied_filters ?? {};

  return (
    <main className="workspace-shell" id="main-content">
      <SiteHeader compact />
      <section className="results-top" aria-labelledby="results-page-title">
        <div>
          <p className="eyebrow">RESULTS · SESSION · EVIDENCE</p>
          <h1 id="results-page-title">当前导购结果</h1>
          <p className="lede">继续追问、调整硬条件或添加图片；结构化结果会覆盖保存到当前设备。</p>
        </div>
        <div className="result-count" aria-label={`当前 ${total} 件结果`}><strong>{total.toString().padStart(2, "0")}</strong><span>RESULTS</span></div>
      </section>

      {hydrated ? (
        <SearchComposer
          busy={busy}
          compact
          initialDraft={snapshot?.draft ?? DEFAULT_DRAFT}
          key={snapshot?.savedAt ?? "new"}
          onSubmit={runSearch}
        />
      ) : <div className="composer-skeleton" aria-label="正在加载搜索表单" />}

      <div className={`system-notice${failure ? " system-notice-error" : ""}`}>
        <p aria-live="polite" role={failure ? "alert" : "status"}>{notice}</p>
        {failure ? <button onClick={() => snapshot && runSearch(snapshot.draft, null)} type="button">重新提交</button> : null}
      </div>

      {snapshot?.agentResults ? (
        <section className="agent-overview" aria-label="Agent 回答与当前条件">
          <div className="answer-copy">
            <span className={`status-badge status-${snapshot.agentResults.status}`}>{statusLabel(snapshot.agentResults.status)}</span>
            <p>{snapshot.agentResults.answer}</p>
            {snapshot.agentResults.warnings.length ? <p className="inline-warning">{snapshot.agentResults.warnings.join("；")}</p> : null}
          </div>
          <div className="condition-editor">
            <h2>当前有效条件</h2>
            <div className="filter-chips">
              {Object.entries(appliedFilters).filter(([, value]) => value != null).map(([field, value]) => (
                <button aria-label={`清除条件：${filterLabels[field] ?? field}`} key={field} onClick={(event) => clearFilter(event, field as FilterField)} type="button">
                  <span>{filterLabels[field] ?? field}</span> {formatFilterValue(field, value)} <b aria-hidden="true">×</b>
                </button>
              ))}
              {snapshot.agentResults.soft_preferences.map((preference) => <span key={preference}>偏好 · {preference}</span>)}
              {!Object.values(appliedFilters).some((value) => value != null) && !snapshot.agentResults.soft_preferences.length ? <em>未设置条件</em> : null}
            </div>
            <p>点击带 × 的硬条件即可清除；其余条件与偏好继续保留。</p>
          </div>
        </section>
      ) : null}

      <section aria-busy={busy} className="results" aria-labelledby="result-list-title">
        <div className="results-heading">
          <div><p className="eyebrow">STRUCTURED PRODUCT CARDS</p><h2 id="result-list-title" ref={resultHeading} tabIndex={-1}>可核验商品</h2></div>
          <p>展示值全部来自结构化响应，不解析回答文本。</p>
        </div>
        {busy ? <LoadingGrid /> : null}
        {!busy && snapshot?.agentResults?.recommendations.length ? (
          <AgentProductGrid comparisonFull={comparison.length >= 4} onToggle={toggleComparison} response={snapshot.agentResults} selectedIds={selectedIds} />
        ) : null}
        {!busy && snapshot?.results?.items.length ? (
          <SearchProductGrid comparisonFull={comparison.length >= 4} onToggle={toggleComparison} response={snapshot.results} selectedIds={selectedIds} />
        ) : null}
        {!busy && snapshot && total === 0 ? (
          <div className="empty-state" role="status">
            <span aria-hidden="true">00</span>
            <div><h3>没有商品同时满足这些条件</h3><p>清除当前硬条件后重新运行相同查询，不会放宽未授权的字段。</p><button className="primary-button" onClick={recoverEmpty} type="button">清除硬条件并重试</button></div>
          </div>
        ) : null}
        {!busy && !snapshot ? (
          <div className="empty-state"><span aria-hidden="true">01</span><div><h3>从一个具体需求开始</h3><p>例如预算、佩戴方式、通勤场景和降噪偏好。</p></div></div>
        ) : null}
        {!busy && snapshot?.agentResults ? <AgentTraceSummary response={snapshot.agentResults} /> : null}
        {!busy && snapshot?.results ? <SearchTraceSummary response={snapshot.results} /> : null}
      </section>

      <ComparisonTray onRemove={removeComparison} products={comparison} />
    </main>
  );
}

function LoadingGrid() {
  return <div className="loading-grid" aria-label="正在加载商品">{[1, 2, 3].map((item) => <div key={item}><span /><span /><span /></div>)}</div>;
}

function clearDraftField(draft: SearchDraft, field: FilterField): SearchDraft {
  if (field === "category") return { ...draft, category: "" };
  if (field === "price_max") return { ...draft, priceMax: "" };
  if (field === "anc") return { ...draft, anc: "" };
  return draft;
}

function formatFilterValue(field: string, value: string | boolean | null): string {
  if (typeof value === "boolean") return value ? "是" : "否";
  if (field === "category") {
    return { over_ear: "头戴式", in_ear: "入耳式", on_ear: "贴耳式", semi_in_ear: "半入耳式", bone_conduction: "骨传导", open_ear: "开放式" }[String(value)] ?? String(value);
  }
  return String(value);
}

function statusLabel(status: "completed" | "needs_clarification" | "degraded"): string {
  if (status === "completed") return "已完成并校验";
  if (status === "needs_clarification") return "需要补充条件";
  return "已降级返回";
}

function restoredNotice(snapshot: SearchSnapshot): string {
  if (snapshot.agentResults?.trace.degraded_reasons.length || snapshot.results?.trace.degraded_reason) {
    return "已恢复最近结果；部分能力发生降级，详情见开发者轨迹。";
  }
  return "已从当前设备恢复最近结果。";
}
