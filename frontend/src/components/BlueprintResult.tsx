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
  imageUrl, stats, originalUrl, onDownload, onRegenerate, onReset,
}: BlueprintResultProps) {
  const brandLabel = stats.brand === "artkal" ? "Artkal" : "Perler";

  return (
    <div className="space-y-6 animate-fade-in">
      {/* success banner */}
      <div className="flex items-center gap-3 px-5 py-4 rounded-2xl bg-emerald-50 border border-emerald-100">
        <CheckCircleIcon className="w-5 h-5 text-emerald-500 shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-[14px] font-semibold text-emerald-700">图纸生成成功</p>
          <p className="text-[13px] text-emerald-600/70">
            {stats.grid_size}×{stats.grid_size} · {stats.total.toLocaleString()} 颗 · {stats.n_colors} 色 · {brandLabel}
          </p>
        </div>
        <button
          onClick={onDownload}
          className="ml-auto shrink-0 inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-[13px] font-semibold
                     bg-emerald-600 text-white hover:bg-emerald-700 transition-colors shadow-sm"
        >
          <DownloadIcon className="w-4 h-4" />
          下载 PNG
        </button>
      </div>

      {/* comparison: original vs blueprint */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-white rounded-2xl border border-neutral-200 overflow-hidden">
          <div className="px-4 py-3 border-b border-neutral-100 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-neutral-400" />
            <h3 className="text-[13px] font-semibold text-neutral-500 uppercase tracking-wider">原图</h3>
          </div>
          <div className="p-4 bg-neutral-50 flex items-center justify-center min-h-[200px]">
            {originalUrl && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={originalUrl} alt="原图" className="max-w-full max-h-[300px] object-contain rounded-lg" />
            )}
          </div>
        </div>
        <div className="bg-white rounded-2xl border border-neutral-200 overflow-hidden">
          <div className="px-4 py-3 border-b border-neutral-100 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            <h3 className="text-[13px] font-semibold text-neutral-500 uppercase tracking-wider">拼豆图纸</h3>
          </div>
          <div className="p-4 bg-neutral-100/50">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={imageUrl} alt="拼豆图纸" className="w-full h-auto rounded-lg shadow-sm" />
          </div>
        </div>
      </div>

      {/* color legend & stats */}
      <div className="bg-white rounded-2xl border border-neutral-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-neutral-100 flex items-center justify-between">
          <div>
            <h3 className="text-[14px] font-semibold text-neutral-800">
              颜色图例
            </h3>
            <p className="text-[12px] text-neutral-400 mt-0.5">
              匹配至 {brandLabel} 色卡
            </p>
          </div>
          <span className="text-[13px] text-neutral-400">
            共 {stats.total.toLocaleString()} 颗 · {stats.n_colors} 色
          </span>
        </div>

        {/* proportional bar */}
        <div className="px-5 py-3 border-b border-neutral-50 flex items-center gap-1 h-6">
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
        <div className="px-5 py-3 max-h-[500px] overflow-y-auto divide-y divide-neutral-50">
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
          className="flex-1 py-3 rounded-xl text-[14px] font-semibold border border-neutral-200
                     text-neutral-600 hover:bg-neutral-50 transition-colors"
        >
          重新生成
        </button>
        <button
          onClick={onReset}
          className="flex-1 py-3 rounded-xl text-[14px] font-semibold border border-neutral-200
                     text-neutral-600 hover:bg-neutral-50 transition-colors"
        >
          制作新图纸
        </button>
      </div>
    </div>
  );
}
