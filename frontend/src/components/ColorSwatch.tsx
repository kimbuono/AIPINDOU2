export interface ColorSwatchProps {
  color: [number, number, number];
  count: number;
  total: number;
}

function rgbToHex([r, g, b]: [number, number, number]): string {
  return `#${r.toString(16).padStart(2, "0")}${g.toString(16).padStart(2, "0")}${b.toString(16).padStart(2, "0")}`;
}

export default function ColorSwatch({ color, count, total }: ColorSwatchProps) {
  const pct = total > 0 ? ((count / total) * 100).toFixed(1) : "0.0";
  const hex = rgbToHex(color);
  const isLight = color[0] + color[1] + color[2] > 600;

  return (
    <div className="flex items-center gap-3 py-2 group" title={hex}>
      {/* swatch */}
      <div
        className="w-8 h-8 rounded-lg shrink-0 border border-black/10 shadow-sm transition-transform duration-150 group-hover:scale-110"
        style={{ backgroundColor: `rgb(${color[0]},${color[1]},${color[2]})` }}
      />
      {/* info */}
      <div className="flex-1 min-w-0 flex items-center justify-between gap-2">
        <span className={`text-[13px] font-mono tabular-nums ${isLight ? "text-neutral-600" : "text-neutral-800"}`}>
          {hex}
        </span>
        <span className="text-[13px] text-neutral-500 tabular-nums shrink-0">
          ×{count.toLocaleString()}
          <span className="text-neutral-400 ml-1">({pct}%)</span>
        </span>
      </div>
      {/* bar */}
      <div className="w-12 h-1 rounded-full bg-neutral-100 shrink-0 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{
            width: `${pct}%`,
            backgroundColor: `rgb(${color[0]},${color[1]},${color[2]})`,
          }}
        />
      </div>
    </div>
  );
}
