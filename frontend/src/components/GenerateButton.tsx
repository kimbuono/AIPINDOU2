"use client";

import { Spinner } from "./Icons";

interface GenerateButtonProps {
  disabled: boolean;
  loading: boolean;
  onClick: () => void;
}

export default function GenerateButton({ disabled, loading, onClick }: GenerateButtonProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled || loading}
      className={`
        w-full py-4 rounded-2xl text-[16px] font-semibold
        flex items-center justify-center gap-3
        transition-all duration-300
        ${disabled || loading
          ? "bg-neutral-100 text-neutral-300 cursor-not-allowed"
          : "bg-neutral-900 text-white hover:bg-neutral-800 hover:shadow-lg hover:shadow-neutral-900/10 active:scale-[0.985]"
        }
      `}
    >
      {loading ? (
        <>
          <Spinner className="w-5 h-5 text-neutral-400" />
          <span className="text-neutral-500">
            正在生成拼豆图纸…
            <span className="block text-[12px] text-neutral-400 font-normal mt-0.5">
              首次生成可能需要等待服务器启动（约 30 秒）
            </span>
          </span>
        </>
      ) : disabled ? (
        "请先上传图片"
      ) : (
        "生成图纸"
      )}
    </button>
  );
}
