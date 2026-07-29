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
      className={`flex w-full items-center justify-center gap-3 rounded-2xl py-4 text-[16px] font-semibold transition-all duration-300 ${
        disabled || loading
          ? "cursor-not-allowed bg-neutral-100 text-neutral-300"
          : "bg-neutral-900 text-white hover:bg-neutral-800 hover:shadow-lg hover:shadow-neutral-900/10 active:scale-[0.985]"
      } `}
    >
      {loading ? (
        <>
          <Spinner className="h-5 w-5 text-neutral-400" />
          <span className="text-neutral-500">正在生成拼豆图纸…</span>
        </>
      ) : disabled ? (
        "请先上传图片"
      ) : (
        "生成图纸"
      )}
    </button>
  );
}
