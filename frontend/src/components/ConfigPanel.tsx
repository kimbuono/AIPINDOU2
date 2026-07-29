"use client";

type GridSize = 16 | 29 | 32 | 48 | 58 | 64;
type ColorCount = 16 | 24 | 32 | 48 | 64 | 80 | 96 | 128 | 256;
type Brand = "artkal" | "perler";

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
  { value: 64, label: "64 色" },
  { value: 80, label: "80 色" },
  { value: 96, label: "96 色" },
  { value: 128, label: "128 色" },
  { value: 256, label: "256 色" },
];

const BRANDS: { value: Brand; label: string; desc: string }[] = [
  { value: "artkal", label: "Artkal", desc: "S 系列 99 色" },
  { value: "perler", label: "Perler", desc: "经典 67 色" },
];

interface ConfigPanelProps {
  gridSize: GridSize;
  colorCount: ColorCount;
  brand: Brand;
  dither: boolean;
  onGridSizeChange: (s: GridSize) => void;
  onColorCountChange: (c: ColorCount) => void;
  onBrandChange: (b: Brand) => void;
  onDitherChange: (d: boolean) => void;
}

export default function ConfigPanel({
  gridSize, colorCount, brand, dither,
  onGridSizeChange, onColorCountChange, onBrandChange, onDitherChange,
}: ConfigPanelProps) {
  return (
    <div className="bg-white rounded-2xl border border-neutral-200 p-6 sm:p-7 space-y-7">
      {/* 色卡品牌 */}
      <fieldset>
        <legend className="flex items-center gap-2 text-[13px] font-semibold text-neutral-500 uppercase tracking-wider mb-3.5">
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <circle cx="13.5" cy="6.5" r="1.5" /><circle cx="17.5" cy="10.5" r="1.5" />
            <circle cx="8.5" cy="7.5" r="1.5" /><circle cx="6.5" cy="12.5" r="1.5" />
            <path d="M12 2C6.49 2 2 6.49 2 12s4.49 10 10 10a2 2 0 0 0 2-2c0-.52-.2-1.01-.56-1.38-.36-.36-.56-.85-.56-1.37 0-1.1.9-2 2-2h2.34c3.53 0 6.4-2.87 6.4-6.4C23.62 5.59 18.64 2 12 2z" />
          </svg>
          色卡品牌
        </legend>
        <div className="grid grid-cols-2 gap-2">
          {BRANDS.map((b) => (
            <button
              key={b.value}
              type="button"
              onClick={() => onBrandChange(b.value)}
              className={`
                py-3 px-4 rounded-xl text-left border transition-all duration-150
                ${brand === b.value
                  ? "bg-neutral-900 text-white border-neutral-900 shadow-sm"
                  : "bg-white text-neutral-600 border-neutral-200 hover:border-neutral-300"
                }
              `}
            >
              <span className="block text-[15px] font-semibold">{b.label}</span>
              <span className={`block text-[12px] mt-0.5 ${brand === b.value ? "text-neutral-400" : "text-neutral-400"}`}>
                {b.desc}
              </span>
            </button>
          ))}
        </div>
        <p className="text-[12px] text-neutral-400 mt-2">
          生成图纸时自动匹配到最近的品牌颜色，图例中显示色号与名称
        </p>
      </fieldset>

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
              <span className="block text-[11px] mt-0.5 opacity-70">
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
            <path d="M12 2C6.49 2 2 6.49 2 12s4.49 10 10 10a2 2 0 0 0 2-2c0-.52-.2-1.01-.56-1.38-.36-.36-.56-.85-.56-1.37 0-1.1.9-2 2-2h2.34c3.53 0 6.4-2.87 6.4-6.4C23.62 5.59 18.64 2 12 2z" />
          </svg>
          最多使用颜色数
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
          自动选择最常用的 N 种颜色，其余映射到最近色
        </p>
      </fieldset>

      {/* 抖动算法 */}
      <fieldset>
        <legend className="flex items-center gap-2 text-[13px] font-semibold text-neutral-500 uppercase tracking-wider mb-3.5">
          高级选项
        </legend>
        <label className="flex items-center justify-between py-2 cursor-pointer">
          <div>
            <span className="text-[14px] font-medium text-neutral-700">Floyd-Steinberg 抖动</span>
            <p className="text-[12px] text-neutral-400 mt-0.5">平滑颜色渐变，减少色块感</p>
          </div>
          <button
            type="button"
            onClick={() => onDitherChange(!dither)}
            className={`
              relative w-11 h-6 rounded-full transition-colors duration-200
              ${dither ? "bg-blue-500" : "bg-neutral-300"}
            `}
          >
            <span
              className={`
                absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform duration-200
                ${dither ? "translate-x-5.5" : "translate-x-0.5"}
              `}
              style={{ left: "1px" }}
            />
          </button>
        </label>
      </fieldset>
    </div>
  );
}

export type { GridSize, ColorCount, Brand };
