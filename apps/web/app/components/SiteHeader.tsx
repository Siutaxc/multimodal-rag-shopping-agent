import Link from "next/link";

export default function SiteHeader({ compact = false }: { compact?: boolean }) {
  return (
    <>
      <a className="skip-link" href="#main-content">
        跳到主要内容
      </a>
      <header className={`masthead${compact ? " masthead-compact" : ""}`}>
        <Link className="brand-mark" href="/" aria-label="ShopLens 首页">
          <span className="brand-orbit" aria-hidden="true" />
          SHOPLENS
        </Link>
        <nav aria-label="主导航">
          <Link href="/">导购首页</Link>
          <Link href="/results">当前结果</Link>
          <Link href="/compare">商品对比</Link>
        </nav>
        <span className="stage-label">STAGE 07 · GROUNDED SHOPPING</span>
      </header>
    </>
  );
}
