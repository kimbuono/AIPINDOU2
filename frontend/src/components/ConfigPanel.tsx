"use client";

type GridSize = 16 | 29 | 32 | 48 | 58 | 64;
type ColorCount = 16 | 24 | 32 | 48;

const SIZES: { value: GridSize; label: string; desc: string }[] = [
  { value: 16, label: "16×16", desc: "迷你" },
  { value: 29, label: "29×29", desc: "小" },
  { value: 32, label: "32×32", desc: "中小" },
  { value: 48, label: "48×48", desc: "标准" },
  { value: 58, label: "58×58", desc: "大" },
  { value: 64, label: "64×64", desc: "超大" },
];

const COLORS: { value: ColorCount; label: string }[] = [
  { value: 16, label: "16 色" },
  { value: 24, label: "24 色" },
  { value: 32, label: "32 色" },
  { value: 48, label: "48 色" },
];

interface ConfigPanelProps {
  gridSize: GridSize;
  colorCount: ColorCount;
  onGridSizeChange: (s: GridSize) => void;
  onColorCountChange: (c: ColorCount) => void;
}

export default function ConfigPanel({
  gridSize, colorCount, onGridSizeChange, onColorCountChange,
}: ConfigPanelProps) {
  return (
    <div className="bg-white rounded-2xl border border-neutral-200 p-6 sm:p-7 space-y-7">
      {/* 图纸尺寸 */}
      <fieldset>
        <legend className="flex items-center gap-2 text-[13px] font-semibold text-neutral-500 uppercase tracking-wider mb-3.5">
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" />
            <rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" />
          </svg>
          图纸尺寸
        </legend>
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
          {SIZES.map((s) => (
            <button
              key={s.value}
              type="button"
              onClick={() => onGridSizeChange(s.value)}
              className={`
                relative py-3 px-2 rounded-xl text-center border transition-all duration-150
                ${gridSize === s.value
                  ? "bg-neutral-900 text-white border-neutral-900 shadow-sm"
                  : "bg-white text-neutral-600 border-neutral-200 hover:border-neutral-300 hover:text-neutral-800"
                }
              `}
            >
              <span className="block text-[14px] font-semibold leading-tight">{s.label}</span>
              <span className={`block text-[11px] mt-0.5 ${gridSize === s.value ? "text-neutral-400" : "text-neutral-400"}`}>
                共 {s.value * s.value} 颗
              </span>
            </button>
          ))}
        </div>
      </fieldset>

      {/* 颜色数量 */}
      <fieldset>
        <legend className="flex items-center gap-2 text-[13px] font-semibold text-neutral-500 uppercase tracking-wider mb-3.5">
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="13.5" cy="6.5" r="1.5" /><circle cx="17.5" cy="10.5" r="1.5" />
            <circle cx="8.5" cy="7.5" r="1.5" /><circle cx="6.5" cy="12.5" r="1.5" />
            <path d="M12 2C6.49 2 2 6.49 2 12s4.49 10 10 10a2 2 0 0 0 2-2c0-.52-.2-1.01-.56-1.38-.36-.36-.56-.85-.56-1.37 0-1.1.9-2 2-2h2.34c3.53 0 6.4-2.87 6.4-6.4C23.62 5.59 18.64 2 12 2z" />
          </svg>
          颜色数量
        </legend>
        <div className="grid grid-cols-4 gap-2">
          {COLORS.map((c) => (
            <button
              key={c.value}
              type="button"
              onClick={() => onColorCountChange(c.value)}
              className={`
                py-3 rounded-xl text-center border transition-all duration-150
                ${colorCount === c.value
                  ? "bg-neutral-900 text-white border-neutral-900 shadow-sm"
                  : "bg-white text-neutral-600 border-neutral-200 hover:border-neutral-300 hover:text-neutral-800"
                }
              `}
            >
              <span className="block text-[15px] font-semibold">{c.label}</span>
            </button>
          ))}
        </div>
        <p className="text-[12px] text-neutral-400 mt-2">
          颜色越多越细腻，但需要的拼豆种类也越多
        </p>
      </fieldset>
    </div>
  );
}
