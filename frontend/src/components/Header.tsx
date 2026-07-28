"use client";

export default function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-black/5 bg-white/80 backdrop-blur-xl supports-[backdrop-filter]:bg-white/60">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-5">
        <a href="/" className="flex items-center gap-2.5 select-none group" aria-label="爱拼豆首页">
          <span className="text-[26px] leading-none transition-transform duration-300 group-hover:scale-110">
            🫘
          </span>
          <span className="text-[17px] font-semibold tracking-tight text-neutral-900">
            爱拼豆
          </span>
        </a>
        <p className="text-[13px] text-neutral-400 hidden sm:block font-medium">
          上传照片，自动生成拼豆图纸
        </p>
      </div>
    </header>
  );
}
