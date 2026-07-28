import { GridIcon, PaletteIcon, DownloadSimpleIcon } from "./Icons";

const FEATURES = [
  {
    icon: <GridIcon className="w-6 h-6" />,
    title: "多种尺寸",
    desc: "16×16 到 64×64，从钥匙扣到大幅装饰画，任意选择适合的尺寸。",
  },
  {
    icon: <PaletteIcon className="w-6 h-6" />,
    title: "智能配色",
    desc: "K-means 色彩量化算法，自动提取画面主色调，颜色还原更准确。",
  },
  {
    icon: <DownloadSimpleIcon className="w-6 h-6" />,
    title: "即用即走",
    desc: "无需注册登录，上传图片即刻生成，下载 PNG 图纸直接开始拼豆。",
  },
];

export default function FeatureCards() {
  return (
    <section className="py-10 px-5">
      <div className="mx-auto max-w-3xl">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {FEATURES.map((f) => (
            <div
              key={f.title}
              className="bg-white rounded-2xl border border-neutral-200 p-6 text-center
                         hover:border-neutral-300 hover:shadow-sm transition-all duration-200"
            >
              <div className="inline-flex items-center justify-center w-10 h-10 rounded-xl bg-neutral-100 text-neutral-600 mb-3">
                {f.icon}
              </div>
              <h3 className="text-[15px] font-semibold text-neutral-800 mb-1.5">{f.title}</h3>
              <p className="text-[13px] text-neutral-500 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
