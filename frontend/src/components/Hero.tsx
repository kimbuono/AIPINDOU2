export default function Hero() {
  return (
    <section className="px-5 py-12 text-center sm:py-16">
      <div className="mx-auto max-w-2xl space-y-5">
        {/* badge */}
        <div className="inline-flex items-center gap-2 rounded-full border border-neutral-200 bg-neutral-100 px-3.5 py-1.5 text-[12px] font-medium text-neutral-500">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          免费在线使用 · 无需注册
        </div>

        {/* headline */}
        <h1 className="text-[32px] leading-[1.15] font-bold tracking-tight text-neutral-900 sm:text-[40px]">
          上传照片，一键生成
          <br />
          <span className="text-neutral-400">专业拼豆图纸</span>
        </h1>

        {/* subheadline */}
        <p className="mx-auto max-w-lg text-[15px] leading-relaxed text-neutral-500 sm:text-[17px]">
          智能色彩分析、自动颜色匹配、精准网格生成。 支持多种尺寸与颜色方案，适配主流拼豆品牌。
        </p>
      </div>
    </section>
  );
}
