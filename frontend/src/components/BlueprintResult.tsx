"use client";

import { DownloadIcon, CheckCircleIcon } from "./Icons";
import ColorSwatch from "./ColorSwatch";

interface BlueprintStats {
  codes: string[];
  names: string[];
  rgb: [number, number, number][];
  counts: number[];
  total: number;
  grid_size: number;
  n_colors: number;
  brand: string;
}

interface BlueprintResultProps {
  imageUrl: string;
  stats: BlueprintStats;
  originalUrl: string | null;
  onDownload: () => void;
  onRegenerate: () => void;
  onReset: () => void;
}

export default function BlueprintResult({
  imageUrl,
  stats,
  originalUrl,
  onDownload,
  onRegenerate,
  onReset,
}: BlueprintResultProps) {
  const brandLabel = stats.brand === "artkal" ? "Artkal" : "Perler";

  return (
    <div className="animate-fade-in space-y-6">
      {/* success banner */}
      <div className="flex items-center gap-3 rounded-2xl border border-emerald-100 bg-emerald-50 px-5 py-4">
        <CheckCircleIcon className="h-5 w-5 shrink-0 text-emerald-500" />
        <div className="min-w-0 flex-1">
          <p className="text-[14px] font-semibold text-emerald-700">图纸生成成功</p>
          <p className="text-[13px] text-emerald-600/70">
            {stats.grid_size}×{stats.grid_size} · {stats.total.toLocaleString()} 颗 ·{" "}
            {stats.n_colors} 色 · {brandLabel}
          </p>
        </div>
        <button
          onClick={onDownload}
          className="ml-auto inline-flex shrink-0 items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2.5 text-[13px] font-semibold text-white shadow-sm transition-colors hover:bg-emerald-700"
        >
          <DownloadIcon className="h-4 w-4" />
          下载 PNG
        </button>
      </div>

      {/* comparison: original vs blueprint */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="overflow-hidden rounded-2xl border border-neutral-200 bg-white">
          <div className="flex items-center gap-2 border-b border-neutral-100 px-4 py-3">
            <span className="h-1.5 w-1.5 rounded-full bg-neutral-400" />
            <h3 className="text-[13px] font-semibold tracking-wider text-neutral-500 uppercase">
              原图
            </h3>
          </div>
          <div className="flex min-h-[200px] items-center justify-center bg-neutral-50 p-4">
            {originalUrl && (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={originalUrl}
                alt="原图"
                className="max-h-[300px] max-w-full rounded-lg object-contain"
              />
            )}
          </div>
        </div>
        <div className="overflow-hidden rounded-2xl border border-neutral-200 bg-white">
          <div className="flex items-center gap-2 border-b border-neutral-100 px-4 py-3">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            <h3 className="text-[13px] font-semibold tracking-wider text-neutral-500 uppercase">
              拼豆图纸
            </h3>
          </div>
          <div className="bg-neutral-100/50 p-4">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={imageUrl} alt="拼豆图纸" className="h-auto w-full rounded-lg shadow-sm" />
          </div>
        </div>
      </div>

      {/* color legend & stats */}
      <div className="overflow-hidden rounded-2xl border border-neutral-200 bg-white">
        <div className="flex items-center justify-between border-b border-neutral-100 px-5 py-4">
          <div>
            <h3 className="text-[14px] font-semibold text-neutral-800">颜色图例</h3>
            <p className="mt-0.5 text-[12px] text-neutral-400">匹配至 {brandLabel} 色卡</p>
          </div>
          <span className="text-[13px] text-neutral-400">
            共 {stats.total.toLocaleString()} 颗 · {stats.n_colors} 色
          </span>
        </div>

        {/* proportional bar */}
        <div className="flex h-6 items-center gap-1 border-b border-neutral-50 px-5 py-3">
          {stats.rgb.map((color, i) => {
            const pct = (stats.counts[i] / stats.total) * 100;
            if (pct < 0.8) return null;
            return (
              <div
                key={i}
                className="h-3 rounded-full transition-all duration-700"
                style={{
                  width: `${pct}%`,
                  backgroundColor: `rgb(${color[0]},${color[1]},${color[2]})`,
                }}
                title={`${stats.codes[i]} ${stats.names[i]}: ${pct.toFixed(1)}%`}
              />
            );
          })}
        </div>

        {/* swatch list */}
        <div className="max-h-[500px] divide-y divide-neutral-50 overflow-y-auto px-5 py-3">
          {stats.rgb.map((color, i) => (
            <ColorSwatch
              key={stats.codes[i]}
              color={color}
              code={stats.codes[i]}
              name={stats.names[i]}
              count={stats.counts[i]}
              total={stats.total}
            />
          ))}
        </div>
      </div>

      {/* actions */}
      <div className="flex items-center gap-3">
        <button
          onClick={onRegenerate}
          className="flex-1 rounded-xl border border-neutral-200 py-3 text-[14px] font-semibold text-neutral-600 transition-colors hover:bg-neutral-50"
        >
          重新生成
        </button>
        <button
          onClick={onReset}
          className="flex-1 rounded-xl border border-neutral-200 py-3 text-[14px] font-semibold text-neutral-600 transition-colors hover:bg-neutral-50"
        >
          制作新图纸
        </button>
      </div>
    </div>
  );
}
