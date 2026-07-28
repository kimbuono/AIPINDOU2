"use client";

import { DownloadIcon, CheckCircleIcon } from "./Icons";
import ColorSwatch from "./ColorSwatch";

interface BlueprintStats {
  palette: [number, number, number][];
  counts: number[];
  total: number;
  grid_size: number;
  n_colors: number;
}

interface BlueprintResultProps {
  imageUrl: string;
  stats: BlueprintStats;
  originalUrl: string | null;
  onDownload: () => void;
}

export default function BlueprintResult({ imageUrl, stats, originalUrl, onDownload }: BlueprintResultProps) {
  return (
    <div className="space-y-6 animate-fade-in">
      {/* success banner */}
      <div className="flex items-center gap-3 px-5 py-4 rounded-2xl bg-emerald-50 border border-emerald-100">
        <CheckCircleIcon className="w-5 h-5 text-emerald-500 shrink-0" />
        <div>
          <p className="text-[14px] font-semibold text-emerald-700">图纸生成成功</p>
          <p className="text-[13px] text-emerald-600/70">
            {stats.grid_size}×{stats.grid_size} 网格 · 共 {stats.total.toLocaleString()} 颗拼豆 · {stats.n_colors} 种颜色
          </p>
        </div>
        <button
          onClick={onDownload}
          className="ml-auto shrink-0 inline-flex items-center gap-2 px-4 py-2 rounded-xl text-[13px] font-semibold
                     bg-emerald-600 text-white hover:bg-emerald-700 transition-colors shadow-sm"
        >
          <DownloadIcon className="w-4 h-4" />
          下载 PNG
        </button>
      </div>

      {/* comparison: original vs blueprint */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* original */}
        <div className="bg-white rounded-2xl border border-neutral-200 overflow-hidden">
          <div className="px-4 py-3 border-b border-neutral-100">
            <h3 className="text-[13px] font-semibold text-neutral-500 uppercase tracking-wider">原图</h3>
          </div>
          <div className="p-4 bg-neutral-50">
            {originalUrl && (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={originalUrl} alt="原图" className="w-full h-auto rounded-lg" />
            )}
          </div>
        </div>

        {/* blueprint */}
        <div className="bg-white rounded-2xl border border-neutral-200 overflow-hidden">
          <div className="px-4 py-3 border-b border-neutral-100">
            <h3 className="text-[13px] font-semibold text-neutral-500 uppercase tracking-wider">拼豆图纸</h3>
          </div>
          <div className="p-4 bg-neutral-100/50">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={imageUrl} alt="拼豆图纸" className="w-full h-auto rounded-lg shadow-sm" />
          </div>
        </div>
      </div>

      {/* color stats & legend */}
      <div className="bg-white rounded-2xl border border-neutral-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-neutral-100 flex items-center justify-between">
          <h3 className="text-[14px] font-semibold text-neutral-800">
            颜色统计与图例
          </h3>
          <span className="text-[13px] text-neutral-400">
            共 {stats.total.toLocaleString()} 颗
          </span>
        </div>

        {/* total bar */}
        <div className="px-5 py-3 border-b border-neutral-50 flex items-center gap-2 h-5">
          {stats.palette.map((color, i) => {
            const pct = (stats.counts[i] / stats.total) * 100;
            if (pct < 1) return null;
            return (
              <div
                key={i}
                className="h-full rounded-full transition-all duration-700"
                style={{
                  width: `${pct}%`,
                  backgroundColor: `rgb(${color[0]},${color[1]},${color[2]})`,
                }}
                title={`${pct.toFixed(1)}%`}
              />
            );
          })}
        </div>

        {/* swatch list */}
        <div className="px-5 py-3 max-h-[400px] overflow-y-auto divide-y divide-neutral-50">
          {stats.palette.map((color, i) => (
            <ColorSwatch
              key={i}
              color={color}
              count={stats.counts[i]}
              total={stats.total}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
