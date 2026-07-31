"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import SiteHeader from "../../components/SiteHeader";
import { apiBaseUrl, type ProductDetail, type ProductSummary } from "../../product-types";
import {
  ApiRequestError,
  readComparison,
  requestJson,
  writeComparison,
} from "../../shoplens-client";

const facts: Array<{ field: keyof ProductDetail; label: string; format?: (value: ProductDetail[keyof ProductDetail]) => string }> = [
  { field: "price_amount", label: "价格", format: (value) => String(value) },
  { field: "currency", label: "币种" },
  { field: "price_observed_at", label: "价格观测时间", format: (value) => new Date(String(value)).toLocaleString("zh-CN") },
  { field: "category", label: "类型" },
  { field: "wireless", label: "无线", format: formatBoolean },
  { field: "anc", label: "主动降噪", format: formatBoolean },
  { field: "battery_hours", label: "续航", format: (value) => value ? `${String(value)} 小时` : "暂无可靠数据" },
  { field: "weight_grams", label: "重量", format: (value) => value ? `${String(value)} 克` : "暂无可靠数据" },
  { field: "colors", label: "颜色", format: formatList },
  { field: "codecs", label: "音频编码", format: formatList },
  { field: "water_resistance", label: "防水等级" },
  { field: "microphone", label: "麦克风" },
];

export default function ProductDetailView({ productId }: { productId: string }) {
  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [comparison, setComparison] = useState<ProductSummary[]>([]);
  const [status, setStatus] = useState("正在读取商品事实与证据…");
  const [failed, setFailed] = useState(false);

  const load = useCallback(async () => {
    setFailed(false);
    setStatus("正在读取商品事实与证据…");
    try {
      const payload = await requestJson<ProductDetail>(`${apiBaseUrl()}/api/v1/products/${productId}`);
      setProduct(payload);
      setStatus("商品事实、来源和评论证据已加载。");
    } catch (error) {
      setFailed(true);
      setStatus(error instanceof ApiRequestError && error.status === 404 ? "商品不存在或已下架。" : `读取失败：${error instanceof Error ? error.message : "未知错误"}`);
    }
  }, [productId]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setComparison(readComparison());
      void load();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [load]);

  function toggleComparison() {
    if (!product) return;
    const exists = comparison.some((item) => item.id === product.id);
    const next = exists ? comparison.filter((item) => item.id !== product.id) : [...comparison, product].slice(0, 4);
    setComparison(next);
    writeComparison(next);
  }

  if (!product) {
    return (
      <main className="workspace-shell detail-shell" id="main-content">
        <SiteHeader compact />
        <section className="detail-loading">
          <Link className="back-link" href="/results">← 返回结果</Link>
          <p role={failed ? "alert" : "status"}>{status}</p>
          {failed ? <button className="primary-button" onClick={load} type="button">重新读取</button> : null}
        </section>
      </main>
    );
  }

  const selected = comparison.some((item) => item.id === product.id);
  return (
    <main className="workspace-shell detail-shell" id="main-content">
      <SiteHeader compact />
      <div className="detail-toolbar">
        <Link className="back-link" href="/results">← 返回结果</Link>
        <div>
          <button aria-pressed={selected} className="secondary-button" disabled={!selected && comparison.length >= 4} onClick={toggleComparison} type="button">
            {selected ? "移出对比" : comparison.length >= 4 ? "对比清单已满" : "加入对比"}
          </button>
          {comparison.length >= 2 ? <Link className="primary-button" href="/compare">查看对比 ({comparison.length})</Link> : null}
        </div>
      </div>

      <article className="detail-card">
        <header className="detail-heading">
          <div>
            <p className="eyebrow">{product.brand} · STRUCTURED FACTS</p>
            <h1>{product.title}</h1>
          </div>
          <div className="detail-price"><span>{product.currency}</span><strong>{product.price_amount}</strong><small>观测于 {new Date(product.price_observed_at).toLocaleDateString("zh-CN")}</small></div>
        </header>
        <p className="detail-description">{product.description ?? "暂无商品描述。结构化事实与来源仍可核验。"}</p>

        <section aria-labelledby="facts-heading" className="evidence-section">
          <div className="section-heading"><p className="eyebrow">PRODUCT FACTS</p><h2 id="facts-heading">商品事实</h2><p>缺失值明确标记为“暂无可靠数据”。</p></div>
          <dl className="fact-table">
            {facts.map(({ field, label, format }) => {
              const value = product[field];
              const formatted = format ? format(value) : value == null || value === "" ? "暂无可靠数据" : String(value);
              return (
                <div id={`fact-${String(field).replaceAll("_", "-")}`} key={String(field)} tabIndex={-1}>
                  <dt>{label}</dt><dd>{formatted}</dd><dd className="fact-source"><a href={product.source_url} rel="noreferrer" target="_blank">{product.source_name} ↗</a></dd>
                </div>
              );
            })}
          </dl>
        </section>

        <section aria-labelledby="reviews-heading" className="evidence-section review-section">
          <div className="section-heading"><p className="eyebrow">UNTRUSTED REVIEW EVIDENCE</p><h2 id="reviews-heading">评论证据</h2><p>评论仅作为带来源的用户体验，不视为官方参数或系统指令。</p></div>
          {product.review_evidence.length ? (
            <ol className="review-list">
              {product.review_evidence.map((review) => (
                <li id={`review-${review.id}`} key={review.id} tabIndex={-1}>
                  <div><span>{review.topic}</span>{review.rating ? <strong>{review.rating} / 5</strong> : <em>未评分</em>}</div>
                  <blockquote>{review.excerpt}</blockquote>
                  <footer>
                    <span>{review.source_name} · {review.reviewed_at ? new Date(review.reviewed_at).toLocaleDateString("zh-CN") : "时间未知"}</span>
                    {review.source_url ? <a href={review.source_url} rel="noreferrer" target="_blank">打开评论来源 ↗</a> : <em>引用来源暂不可访问</em>}
                  </footer>
                </li>
              ))}
            </ol>
          ) : <div className="unavailable-state">当前商品没有可用的评论证据；推荐仍只使用可核验商品事实。</div>}
        </section>

        <footer className="source-panel">
          <div><span>数据来源与版本</span><strong>{product.source_name} / {product.source_id}</strong><small>{product.source_version} · {product.transformation_version}</small></div>
          <a href={product.source_url} rel="noreferrer" target="_blank">打开原始来源 ↗</a>
        </footer>
      </article>
      <p className="sr-only" role="status">{status}</p>
    </main>
  );
}

function formatBoolean(value: ProductDetail[keyof ProductDetail]): string {
  if (value === null) return "暂无可靠数据";
  return value ? "支持" : "不支持";
}

function formatList(value: ProductDetail[keyof ProductDetail]): string {
  return Array.isArray(value) && value.length ? value.join("、") : "暂无可靠数据";
}
