"use client";

import Link from "next/link";

import type {
  AgentEvidence,
  AssistantResponse,
  GroundedStatement,
  ProductSummary,
  SearchResponse,
} from "../product-types";
import { evidenceAnchor } from "../shoplens-client";

const categoryLabels: Record<string, string> = {
  in_ear: "入耳式",
  semi_in_ear: "半入耳式",
  over_ear: "头戴式",
  on_ear: "贴耳式",
  bone_conduction: "骨传导",
  open_ear: "开放式",
};

function ComparisonButton({
  product,
  selected,
  disabled,
  onToggle,
}: {
  product: ProductSummary;
  selected: boolean;
  disabled: boolean;
  onToggle: (product: ProductSummary) => void;
}) {
  return (
    <button
      aria-pressed={selected}
      className="compare-toggle"
      disabled={!selected && disabled}
      onClick={() => onToggle(product)}
      type="button"
    >
      {selected ? "已加入对比 · 移出" : disabled ? "对比已满" : "加入对比"}
    </button>
  );
}

export function AgentProductGrid({
  response,
  selectedIds,
  comparisonFull,
  onToggle,
}: {
  response: AssistantResponse;
  selectedIds: Set<string>;
  comparisonFull: boolean;
  onToggle: (product: ProductSummary) => void;
}) {
  const evidenceById = new Map(response.evidence.map((item) => [item.id, item]));
  return (
    <ol className="result-grid" aria-label="Agent 推荐商品">
      {response.recommendations.map((item) => (
        <li key={item.product.id}>
          <div className="card-kicker">
            <span className="rank">#{item.rank}</span>
            <span>{categoryLabels[item.product.category] ?? item.product.category}</span>
          </div>
          <p className="product-meta">{item.product.brand}</p>
          <h3>{item.product.title}</h3>
          <p className="price">
            <span>{item.product.currency}</span> {item.product.price_amount}
          </p>
          <dl className="mini-facts">
            <div><dt>ANC</dt><dd>{formatBoolean(item.product.anc, "支持", "不支持")}</dd></div>
            <div><dt>续航</dt><dd>{item.product.battery_hours ? `${item.product.battery_hours} h` : "暂无"}</dd></div>
            <div><dt>重量</dt><dd>{item.product.weight_grams ? `${item.product.weight_grams} g` : "暂无"}</dd></div>
          </dl>
          <StatementGroup
            evidenceById={evidenceById}
            label="匹配与推荐依据"
            productId={item.product.id}
            statements={[...item.matched_requirements, ...item.reasons]}
          />
          {item.tradeoffs.length ? (
            <StatementGroup
              evidenceById={evidenceById}
              label="需要权衡"
              productId={item.product.id}
              statements={item.tradeoffs}
              tradeoff
            />
          ) : null}
          <div className="card-actions">
            <ComparisonButton
              disabled={comparisonFull}
              onToggle={onToggle}
              product={item.product}
              selected={selectedIds.has(item.product.id)}
            />
            <Link href={`/products/${item.product.id}`}>查看事实与全部证据 →</Link>
          </div>
        </li>
      ))}
    </ol>
  );
}

export function SearchProductGrid({
  response,
  selectedIds,
  comparisonFull,
  onToggle,
}: {
  response: SearchResponse;
  selectedIds: Set<string>;
  comparisonFull: boolean;
  onToggle: (product: ProductSummary) => void;
}) {
  return (
    <ol className="result-grid" aria-label="检索商品">
      {response.items.map((item) => (
        <li key={item.product.id}>
          <div className="card-kicker">
            <span className="rank">#{item.rank}</span>
            <span>{categoryLabels[item.product.category] ?? item.product.category}</span>
          </div>
          <p className="product-meta">{item.product.brand}</p>
          <h3>{item.product.title}</h3>
          <p className="price"><span>{item.product.currency}</span> {item.product.price_amount}</p>
          <dl className="mini-facts">
            <div><dt>无线</dt><dd>{formatBoolean(item.product.wireless, "是", "否")}</dd></div>
            <div><dt>ANC</dt><dd>{formatBoolean(item.product.anc, "支持", "不支持")}</dd></div>
            <div><dt>续航</dt><dd>{item.product.battery_hours ? `${item.product.battery_hours} h` : "暂无"}</dd></div>
          </dl>
          <p className="retrieval-score">{scoreLabel(item)}</p>
          <div className="card-actions">
            <ComparisonButton
              disabled={comparisonFull}
              onToggle={onToggle}
              product={item.product}
              selected={selectedIds.has(item.product.id)}
            />
            <Link href={`/products/${item.product.id}`}>查看事实与来源 →</Link>
          </div>
        </li>
      ))}
    </ol>
  );
}

function StatementGroup({
  statements,
  evidenceById,
  productId,
  label,
  tradeoff = false,
}: {
  statements: GroundedStatement[];
  evidenceById: Map<string, AgentEvidence>;
  productId: string;
  label: string;
  tradeoff?: boolean;
}) {
  if (!statements.length) return null;
  return (
    <section className={`statement-group${tradeoff ? " statement-tradeoff" : ""}`} aria-label={label}>
      <h4>{label}</h4>
      <ul className="evidence-list">
        {statements.map((statement, index) => (
          <li key={`${statement.text}-${index}`}>
            <span>{statement.text}</span>
            <span className="citation-row">
              {statement.evidence_ids.map((id) => {
                const item = evidenceById.get(id);
                if (!item || !item.available) {
                  return <em key={id} title={id}>证据暂不可用</em>;
                }
                const anchor = evidenceAnchor(item.kind, item.field, item.id);
                return (
                  <Link href={`/products/${productId}#${anchor}`} key={id}>
                    定位证据
                  </Link>
                );
              })}
            </span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function formatBoolean(value: boolean | null, yes: string, no: string): string {
  if (value === null) return "暂无";
  return value ? yes : no;
}

function scoreLabel(item: SearchResponse["items"][number]): string {
  if (item.fusion_score != null) return `图文 RRF · ${item.fusion_score.toFixed(4)}`;
  if (item.image_score != null) return `图片相似 · ${item.image_score.toFixed(3)}`;
  if (item.rerank_score != null) return `重排 · ${item.rerank_score.toFixed(3)}`;
  if (item.rrf_score != null) return `RRF · ${item.rrf_score.toFixed(4)}`;
  if (item.dense_score != null) return `稠密召回 · ${item.dense_score.toFixed(3)}`;
  return `词法召回 · ${(item.lexical_score ?? 0).toFixed(3)}`;
}
