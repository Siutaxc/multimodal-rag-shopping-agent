import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SHOPLENS_SITE_URL ?? "http://localhost:3000",
  ),
  title: {
    default: "ShopLens · 可核验多模态耳机导购",
    template: "%s · ShopLens",
  },
  description: "以结构化硬过滤、图文检索和可定位证据完成耳机推荐与商品对比。",
  openGraph: {
    title: "ShopLens · 选耳机，别靠猜。",
    description: "结构化硬过滤、图文检索与可定位证据驱动的耳机导购。",
    images: [{ url: "/og.png", width: 1200, height: 630, alt: "ShopLens 可核验多模态耳机导购" }],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "ShopLens · 选耳机，别靠猜。",
    description: "结构化硬过滤、图文检索与可定位证据驱动的耳机导购。",
    images: ["/og.png"],
  },
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html data-scroll-behavior="smooth" lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
