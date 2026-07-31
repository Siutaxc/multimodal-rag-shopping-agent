"use client";

import Link from "next/link";

import type { ProductSummary } from "../product-types";

export default function ComparisonTray({
  products,
  onRemove,
}: {
  products: ProductSummary[];
  onRemove: (productId: string) => void;
}) {
  if (!products.length) return null;
  return (
    <aside aria-label="商品对比栏" className="comparison-tray">
      <div>
        <strong>对比清单</strong>
        <span>{products.length}/4 · 至少选择 2 件</span>
      </div>
      <ul>
        {products.map((product) => (
          <li key={product.id}>
            <span>{product.title}</span>
            <button aria-label={`移出对比：${product.title}`} onClick={() => onRemove(product.id)} type="button">
              移除
            </button>
          </li>
        ))}
      </ul>
      {products.length >= 2 ? (
        <Link className="primary-button" href="/compare">
          对比 {products.length} 件商品
        </Link>
      ) : (
        <span className="disabled-button" aria-disabled="true">
          再选 1 件
        </span>
      )}
    </aside>
  );
}
