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
    <div className="flex items-center gap-3 py-2.5 group">
      {/* swatch */}
      <div
        className="w-9 h-9 rounded-lg shrink-0 border border-black/10 shadow-sm transition-transform duration-150 group-hover:scale-110"
        style={{ backgroundColor: `rgb(${color[0]},${color[1]},${color[2]})` }}
      />
      {/* code + name */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-[13px] font-semibold text-neutral-800 tabular-nums font-mono">
            {code}
          </span>
          <span className="text-[13px] text-neutral-500">{name}</span>
        </div>
      </div>
      {/* count + bar */}
      <div className="flex items-center gap-3 shrink-0">
        <span className="text-[13px] text-neutral-500 tabular-nums text-right w-12">
          ×{count.toLocaleString()}
        </span>
        <span className="text-[12px] text-neutral-400 tabular-nums w-12 text-right">
          {pct}%
        </span>
        <div className="w-14 h-1.5 rounded-full bg-neutral-100 overflow-hidden">
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
