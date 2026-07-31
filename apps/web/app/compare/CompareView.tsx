"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import SiteHeader from "../components/SiteHeader";
import { apiBaseUrl, type AgentEvidence, type AssistantResponse, type ProductSummary } from "../product-types";
import {
  ApiRequestError,
  evidenceAnchor,
  readComparison,
  readLocalValue,
  requestJson,
  STORAGE_KEYS,
  writeComparison,
} from "../shoplens-client";

export default function CompareView() {
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [response, setResponse] = useState<AssistantResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState("正在读取对比清单…");
  const [failed, setFailed] = useState(false);

  const compare = useCallback(async (nextProducts: ProductSummary[]) => {
    if (nextProducts.length < 2) {
      setResponse(null);
      setStatus("至少选择 2 件商品才能生成统一字段对比。");
      return;
    }
    setBusy(true);
    setFailed(false);
    setStatus("正在加载统一字段并核验每个单元格的证据…");
    try {
      const sessionId = readLocalValue<string>(STORAGE_KEYS.session);
      const payload = await requestJson<AssistantResponse>(`${apiBaseUrl()}/api/v1/products/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_ids: nextProducts.map((product) => product.id),
          session_id: sessionId ?? undefined,
        }),
      });
      setResponse(payload);
      setStatus(payload.trace.degraded_reasons.length ? "对比已返回，但部分能力降级；结构化单元格仍可核验。" : `已完成 ${nextProducts.length} 件商品对比。`);
    } catch (error) {
      setFailed(true);
      setStatus(error instanceof ApiRequestError && error.kind === "timeout" ? error.message : `对比失败：${error instanceof Error ? error.message : "未知错误"}`);
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const restored = readComparison();
      setProducts(restored);
      void compare(restored);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [compare]);

  function removeProduct(productId: string) {
    const next = products.filter((product) => product.id !== productId);
    setProducts(next);
    writeComparison(next);
    void compare(next);
  }

  const evidenceById = useMemo(() => new Map((response?.evidence ?? []).map((item) => [item.id, item])), [response]);

  return (
    <main className="workspace-shell compare-shell" id="main-content">
      <SiteHeader compact />
      <section className="results-top" aria-labelledby="compare-title">
        <div><p className="eyebrow">2–4 PRODUCTS · SAME FIELDS</p><h1 id="compare-title">商品对比</h1><p className="lede">每个单元格来自结构化商品事实，并绑定相应证据 ID。</p></div>
        <div className="result-count"><strong>{products.length.toString().padStart(2, "0")}</strong><span>SELECTED</span></div>
      </section>

      <div className={`system-notice${failed ? " system-notice-error" : ""}`}>
        <p aria-live="polite" role={failed ? "alert" : "status"}>{status}</p>
        {failed ? <button onClick={() => compare(products)} type="button">重新加载</button> : null}
      </div>

      {products.length ? (
        <ul className="compare-product-list" aria-label="已选商品">
          {products.map((product, index) => (
            <li key={product.id}><span>{String(index + 1).padStart(2, "0")}</span><div><strong>{product.title}</strong><small>{product.brand}</small></div><button aria-label={`移出对比：${product.title}`} onClick={() => removeProduct(product.id)} type="button">移除</button></li>
          ))}
        </ul>
      ) : null}

      {busy ? <div className="table-skeleton" aria-label="正在加载对比表" /> : null}
      {!busy && response?.comparison ? (
        <div className="comparison-table-wrap" tabIndex={0} role="region" aria-label="商品参数对比，可横向滚动">
          <table className="comparison-table">
            <caption>ShopLens 商品结构化事实对比</caption>
            <thead><tr><th scope="col">对比字段</th>{products.map((product) => <th scope="col" key={product.id}><Link href={`/products/${product.id}`}>{product.title}</Link><span>{product.brand}</span></th>)}</tr></thead>
            <tbody>
              {response.comparison.rows.map((row) => (
                <tr key={row.field}>
                  <th scope="row">{row.label}</th>
                  {products.map((product) => {
                    const cell = row.values.find((value) => value.product_id === product.id);
                    const evidence = cell ? evidenceById.get(cell.evidence_id) : undefined;
                    return <ComparisonCell cell={cell} evidence={evidence} field={row.field} key={product.id} productId={product.id} />;
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {!busy && products.length < 2 ? (
        <div className="empty-state"><span aria-hidden="true">02</span><div><h2>还需要 {2 - products.length} 件商品</h2><p>回到结果页，使用商品卡上的“加入对比”。最多可选择 4 件。</p><Link className="primary-button" href="/results">返回结果选商品</Link></div></div>
      ) : null}

      {response ? (
        <aside className="compare-audit"><div><span>引用校验</span><strong>{response.trace.citation_validation.valid ? "通过" : "安全回退"}</strong></div><div><span>结构化字段</span><strong>{response.comparison?.rows.length ?? 0}</strong></div><div><span>工具步骤</span><strong>{response.trace.tool_steps.length}/4</strong></div><Link href={`/traces/${response.trace_id}`}>查看完整轨迹 →</Link></aside>
      ) : null}
    </main>
  );
}

function ComparisonCell({
  cell,
  evidence,
  field,
  productId,
}: {
  cell: { product_id: string; value: string | boolean | string[] | null; evidence_id: string } | undefined;
  evidence: AgentEvidence | undefined;
  field: string;
  productId: string;
}) {
  if (!cell) return <td><span className="missing-value">暂无可靠数据</span></td>;
  const formatted = Array.isArray(cell.value) ? (cell.value.join("、") || "暂无可靠数据") : typeof cell.value === "boolean" ? (cell.value ? "支持" : "不支持") : cell.value ?? "暂无可靠数据";
  const anchor = evidence ? evidenceAnchor(evidence.kind, evidence.field, evidence.id) : `fact-${field.replaceAll("_", "-")}`;
  return (
    <td>
      <span className={cell.value == null ? "missing-value" : undefined}>{formatted}</span>
      {evidence?.available === false ? <em>证据记录存在，值不可用</em> : <Link href={`/products/${productId}#${anchor}`}>核验单元格 →</Link>}
    </td>
  );
}
