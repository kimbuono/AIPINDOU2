import { UploadIcon, GridIcon, DownloadSimpleIcon } from "./Icons";

const STEPS = [
  {
    icon: <UploadIcon className="w-5 h-5" />,
    title: "上传图片",
    desc: "拖拽或点击上传你的照片，支持 JPG、PNG、WebP 格式",
  },
  {
    icon: <GridIcon className="w-5 h-5" />,
    title: "选择参数",
    desc: "选择图纸尺寸和颜色数量，实时预览配置效果",
  },
  {
    icon: <DownloadSimpleIcon className="w-5 h-5" />,
    title: "下载图纸",
    desc: "一键生成拼豆图纸，下载 PNG 即可开始制作",
  },
];

export default function HowItWorks() {
  return (
    <section className="py-10 px-5">
      <div className="mx-auto max-w-3xl">
        <h2 className="text-center text-[20px] font-bold text-neutral-800 mb-8">使用流程</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {STEPS.map((step, i) => (
            <div key={step.title} className="relative text-center">
              {/* connector line */}
              {i < STEPS.length - 1 && (
                <div className="hidden sm:block absolute top-6 left-[60%] w-[80%] h-px bg-neutral-200" />
              )}
              {/* number */}
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-2xl bg-neutral-900 text-white text-[15px] font-bold mb-4 relative z-10">
                {i + 1}
              </div>
              {/* icon + text */}
              <div className="inline-flex items-center gap-2 mb-2 text-neutral-500">{step.icon}</div>
              <h3 className="text-[15px] font-semibold text-neutral-800 mb-1">{step.title}</h3>
              <p className="text-[13px] text-neutral-500 leading-relaxed">{step.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
