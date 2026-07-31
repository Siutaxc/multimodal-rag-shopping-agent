"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import SearchComposer from "./components/SearchComposer";
import SiteHeader from "./components/SiteHeader";
import type { SearchDraft } from "./product-types";
import {
  ApiRequestError,
  DEFAULT_DRAFT,
  executeSearch,
  readLocalValue,
  saveSearchExecution,
  STORAGE_KEYS,
} from "./shoplens-client";

export default function Home() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("默认 Fixture 模式无需付费模型，可稳定演示完整链路。");

  async function startSearch(draft: SearchDraft, image: File | null) {
    setBusy(true);
    setMessage(image ? "正在验证图片并执行有界导购…" : "正在解析需求、检索商品并核验证据…");
    try {
      const sessionId = readLocalValue<string>(STORAGE_KEYS.session);
      const execution = await executeSearch({ draft, image, sessionId });
      saveSearchExecution(draft, execution);
      router.push("/results");
    } catch (error) {
      const label = error instanceof ApiRequestError && error.kind === "timeout"
        ? error.message
        : `暂时无法完成导购：${error instanceof Error ? error.message : "未知错误"}`;
      setMessage(label);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main id="main-content">
      <SiteHeader />
      <section className="search-hero" aria-labelledby="page-title">
        <div className="hero-grid">
          <div>
            <p className="eyebrow">MULTIMODAL RAG · EVIDENCE FIRST</p>
            <h1 id="page-title">选耳机，<span>别靠猜。</span></h1>
          </div>
          <div className="hero-copy">
            <p>
              预算、类型和降噪由数据库硬过滤；每个推荐理由都能定位到商品事实或带来源的评论证据。
            </p>
            <dl className="hero-metrics" aria-label="系统边界">
              <div><dt>MAX</dt><dd>4 个工具步骤</dd></div>
              <div><dt>FACTS</dt><dd>结构化渲染</dd></div>
              <div><dt>FAILURE</dt><dd>确定性降级</dd></div>
            </dl>
          </div>
        </div>

        <SearchComposer busy={busy} initialDraft={DEFAULT_DRAFT} onSubmit={startSearch} />
        <div className="hero-status-row">
          <p aria-live="polite" role="status">{message}</p>
          <Link href="/results">恢复上次会话 →</Link>
        </div>
      </section>

      <section className="proof-strip" aria-labelledby="proof-title">
        <p className="eyebrow">WHY SHOPLENS</p>
        <h2 id="proof-title">检索、证据和决策边界，都摆在台面上。</h2>
        <div className="proof-grid">
          <article><span>01</span><h3>硬条件先过滤</h3><p>价格、类型、ANC 等白名单字段由参数化查询执行，不交给模型猜。</p></article>
          <article><span>02</span><h3>多路召回可追踪</h3><p>词法、文本向量、图片向量、RRF 与重排候选变化可展开查看。</p></article>
          <article><span>03</span><h3>回答必须有证据</h3><p>前端只读结构化商品与证据字段，不从自然语言答案反推事实。</p></article>
        </div>
      </section>
    </main>
  );
}
