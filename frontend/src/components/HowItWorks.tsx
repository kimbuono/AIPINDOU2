import { UploadIcon, GridIcon, DownloadSimpleIcon } from "./Icons";

const STEPS = [
  {
    icon: <UploadIcon className="h-5 w-5" />,
    title: "上传图片",
    desc: "拖拽或点击上传你的照片，支持 JPG、PNG、WebP 格式",
  },
  {
    icon: <GridIcon className="h-5 w-5" />,
    title: "选择参数",
    desc: "选择图纸尺寸和颜色数量，实时预览配置效果",
  },
  {
    icon: <DownloadSimpleIcon className="h-5 w-5" />,
    title: "下载图纸",
    desc: "一键生成拼豆图纸，下载 PNG 即可开始制作",
  },
];

export default function HowItWorks() {
  return (
    <section className="px-5 py-10">
      <div className="mx-auto max-w-3xl">
        <h2 className="mb-8 text-center text-[20px] font-bold text-neutral-800">使用流程</h2>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
          {STEPS.map((step, i) => (
            <div key={step.title} className="relative text-center">
              {/* connector line */}
              {i < STEPS.length - 1 && (
                <div className="absolute top-6 left-[60%] hidden h-px w-[80%] bg-neutral-200 sm:block" />
              )}
              {/* number */}
              <div className="relative z-10 mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-neutral-900 text-[15px] font-bold text-white">
                {i + 1}
              </div>
              {/* icon + text */}
              <div className="mb-2 inline-flex items-center gap-2 text-neutral-500">
                {step.icon}
              </div>
              <h3 className="mb-1 text-[15px] font-semibold text-neutral-800">{step.title}</h3>
              <p className="text-[13px] leading-relaxed text-neutral-500">{step.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
