export interface ColorSwatchProps {
  color: [number, number, number];
  code: string;
  name: string;
  count: number;
  total: number;
}

export default function ColorSwatch({ color, code, name, count, total }: ColorSwatchProps) {
  const pct = total > 0 ? ((count / total) * 100).toFixed(1) : "0.0";

  return (
    <div className="group flex items-center gap-3 py-2.5">
      {/* swatch */}
      <div
        className="h-9 w-9 shrink-0 rounded-lg border border-black/10 shadow-sm transition-transform duration-150 group-hover:scale-110"
        style={{ backgroundColor: `rgb(${color[0]},${color[1]},${color[2]})` }}
      />
      {/* code + name */}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[13px] font-semibold text-neutral-800 tabular-nums">
            {code}
          </span>
          <span className="text-[13px] text-neutral-500">{name}</span>
        </div>
      </div>
      {/* count + bar */}
      <div className="flex shrink-0 items-center gap-3">
        <span className="w-12 text-right text-[13px] text-neutral-500 tabular-nums">
          ×{count.toLocaleString()}
        </span>
        <span className="w-12 text-right text-[12px] text-neutral-400 tabular-nums">{pct}%</span>
        <div className="h-1.5 w-14 overflow-hidden rounded-full bg-neutral-100">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{
              width: `${pct}%`,
              backgroundColor: `rgb(${color[0]},${color[1]},${color[2]})`,
            }}
          />
        </div>
      </div>
    </div>
  );
}
