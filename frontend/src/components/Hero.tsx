export default function Hero() {
  return (
    <section className="text-center py-12 sm:py-16 px-5">
      <div className="mx-auto max-w-2xl space-y-5">
        {/* badge */}
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-neutral-100 border border-neutral-200 text-[12px] font-medium text-neutral-500">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
          免费在线使用 · 无需注册
        </div>

        {/* headline */}
        <h1 className="text-[32px] sm:text-[40px] font-bold tracking-tight text-neutral-900 leading-[1.15]">
          上传照片，一键生成
          <br />
          <span className="text-neutral-400">专业拼豆图纸</span>
        </h1>

        {/* subheadline */}
        <p className="text-[15px] sm:text-[17px] text-neutral-500 leading-relaxed max-w-lg mx-auto">
          智能色彩分析、自动颜色匹配、精准网格生成。
          支持多种尺寸与颜色方案，适配主流拼豆品牌。
        </p>
      </div>
    </section>
  );
}
