import { GridIcon, PaletteIcon, DownloadSimpleIcon } from "./Icons";

const FEATURES = [
  {
    icon: <GridIcon className="h-6 w-6" />,
    title: "多种尺寸",
    desc: "16×16 到 64×64，从钥匙扣到大幅装饰画，任意选择适合的尺寸。",
  },
  {
    icon: <PaletteIcon className="h-6 w-6" />,
    title: "智能配色",
    desc: "K-means 色彩量化算法，自动提取画面主色调，颜色还原更准确。",
  },
  {
    icon: <DownloadSimpleIcon className="h-6 w-6" />,
    title: "即用即走",
    desc: "无需注册登录，上传图片即刻生成，下载 PNG 图纸直接开始拼豆。",
  },
];

export default function FeatureCards() {
  return (
    <section className="px-5 py-10">
      <div className="mx-auto max-w-3xl">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="rounded-2xl border border-neutral-200 bg-white p-6 text-center transition-all duration-200 hover:border-neutral-300 hover:shadow-sm"
            >
              <div className="mb-3 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-neutral-100 text-neutral-600">
                {f.icon}
              </div>
              <h3 className="mb-1.5 text-[15px] font-semibold text-neutral-800">{f.title}</h3>
              <p className="text-[13px] leading-relaxed text-neutral-500">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
