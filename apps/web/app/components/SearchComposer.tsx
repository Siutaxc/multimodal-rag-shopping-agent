"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useEffect, useRef, useState } from "react";

import type { SearchDraft } from "../product-types";

const categoryLabels: Record<string, string> = {
  in_ear: "入耳式",
  semi_in_ear: "半入耳式",
  over_ear: "头戴式",
  on_ear: "贴耳式",
  bone_conduction: "骨传导",
  open_ear: "开放式",
};

export default function SearchComposer({
  initialDraft,
  busy,
  compact = false,
  onSubmit,
}: {
  initialDraft: SearchDraft;
  busy: boolean;
  compact?: boolean;
  onSubmit: (draft: SearchDraft, image: File | null) => Promise<void>;
}) {
  const [draft, setDraft] = useState(initialDraft);
  const [image, setImage] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [imageError, setImageError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    return () => {
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setImageError(null);
    if (draft.searchKind !== "image" && !draft.query.trim()) {
      setImageError("请输入导购需求或搜索词。");
      return;
    }
    if (["image", "multimodal"].includes(draft.searchKind) && !image) {
      setImageError("这种输入方式需要一张参考图片。");
      fileInput.current?.focus();
      return;
    }
    await onSubmit({ ...draft, query: draft.query.trim() }, image);
  }

  function chooseImage(event: ChangeEvent<HTMLInputElement>) {
    const next = event.target.files?.[0] ?? null;
    setImageError(null);
    if (next && !["image/jpeg", "image/png", "image/webp"].includes(next.type)) {
      setImageError("图片格式不受支持，请选择 JPEG、PNG 或 WebP。");
      event.target.value = "";
      return;
    }
    if (next && next.size > 5 * 1024 * 1024) {
      setImageError("图片超过 5 MB，请压缩后重试。");
      event.target.value = "";
      return;
    }
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setImage(next);
    setPreviewUrl(next ? URL.createObjectURL(next) : null);
  }

  function removeImage() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setImage(null);
    setImageError(null);
    if (fileInput.current) fileInput.current.value = "";
    fileInput.current?.focus();
  }

  return (
    <form
      aria-busy={busy}
      className={`search-form${compact ? " search-form-compact" : ""}`}
      onSubmit={submit}
    >
      <label className="query-field">
        <span>导购需求 / 搜索词 / 图片补充条件</span>
        <textarea
          aria-label="搜索词"
          maxLength={300}
          onChange={(event) => setDraft({ ...draft, query: event.target.value })}
          placeholder="例如：预算 1000 元，头戴式降噪，通勤且戴眼镜舒适"
          rows={compact ? 2 : 3}
          value={draft.query}
        />
      </label>

      <fieldset className="input-mode-fieldset">
        <legend>输入方式</legend>
        <div className="segmented-control">
          {[
            ["agent", "Agent 导购"],
            ["text", "纯文本"],
            ["image", "纯图片"],
            ["multimodal", "图片 + 文字"],
          ].map(([value, label]) => (
            <label key={value}>
              <input
                checked={draft.searchKind === value}
                name="search-kind"
                onChange={() =>
                  setDraft({ ...draft, searchKind: value as SearchDraft["searchKind"] })
                }
                type="radio"
                value={value}
              />
              <span>{label}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <div className="image-input-row">
        <label className="image-picker">
          <span>参考图片（JPEG / PNG / WebP，最大 5 MB）</span>
          <input
            accept="image/jpeg,image/png,image/webp"
            aria-describedby={imageError ? "image-error" : undefined}
            aria-label="参考图片"
            onChange={chooseImage}
            ref={fileInput}
            type="file"
          />
        </label>
        {previewUrl ? (
          <div className="image-preview-wrap">
            {/* Blob URLs are local previews and intentionally bypass optimization. */}
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img alt={`参考图片预览：${image?.name ?? "已选择图片"}`} className="image-preview" src={previewUrl} />
            <button className="image-remove" onClick={removeImage} type="button">
              删除图片
            </button>
          </div>
        ) : null}
      </div>
      {imageError ? (
        <p className="field-error" id="image-error" role="alert">
          {imageError}
        </p>
      ) : null}

      <div className="filter-row">
        <label>
          <span>检索模式</span>
          <select
            aria-label="检索模式"
            disabled={draft.searchKind === "agent"}
            onChange={(event) =>
              setDraft({ ...draft, mode: event.target.value as SearchDraft["mode"] })
            }
            value={draft.mode}
          >
            <option value="rerank">混合 + 重排</option>
            <option value="rrf">RRF 融合</option>
            <option value="dense">仅稠密</option>
            <option value="lexical">仅词法</option>
          </select>
        </label>
        <label>
          <span>类型</span>
          <select
            aria-label="类型"
            onChange={(event) => setDraft({ ...draft, category: event.target.value })}
            value={draft.category}
          >
            <option value="">全部</option>
            {Object.entries(categoryLabels).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>最高价格（CNY）</span>
          <input
            aria-label="最高价格"
            min="0"
            onChange={(event) => setDraft({ ...draft, priceMax: event.target.value })}
            placeholder="不限"
            step="0.01"
            type="number"
            value={draft.priceMax}
          />
        </label>
        <label>
          <span>主动降噪</span>
          <select
            aria-label="主动降噪"
            onChange={(event) =>
              setDraft({ ...draft, anc: event.target.value as SearchDraft["anc"] })
            }
            value={draft.anc}
          >
            <option value="">不限</option>
            <option value="true">必须支持</option>
            <option value="false">必须不支持</option>
          </select>
        </label>
        <button className="primary-button" disabled={busy} type="submit">
          {busy ? "正在核验…" : draft.searchKind === "agent" ? "开始导购" : "开始检索"}
        </button>
      </div>
    </form>
  );
}
