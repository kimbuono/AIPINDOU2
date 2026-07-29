"use client";

import { useRef, useState, useCallback, type DragEvent, type ChangeEvent } from "react";
import Image from "next/image";
import { ImageIcon, TrashIcon } from "./Icons";

interface UploadZoneProps {
  file: File | null;
  previewUrl: string | null;
  onFileAccepted: (file: File) => void;
  onFileRemove: () => void;
}

export default function UploadZone({
  file,
  previewUrl,
  onFileAccepted,
  onFileRemove,
}: UploadZoneProps) {
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const validateAndAccept = useCallback(
    (f: File) => {
      const valid = ["image/jpeg", "image/png", "image/webp"];
      if (!valid.includes(f.type)) {
        setError("不支持的图片格式，仅支持 JPG、PNG、WebP");
        return;
      }
      if (f.size > 10 * 1024 * 1024) {
        setError("图片大小不能超过 10 MB");
        return;
      }
      setError(null);
      onFileAccepted(f);
    },
    [onFileAccepted],
  );

  const onDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const f = e.dataTransfer.files?.[0];
      if (f) validateAndAccept(f);
    },
    [validateAndAccept],
  );

  const onChange = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) validateAndAccept(f);
  };

  return (
    <div className="space-y-3">
      {/* upload area */}
      <div
        className={`relative cursor-pointer rounded-2xl border-2 border-dashed p-10 text-center transition-all duration-200 select-none sm:p-14 ${
          dragOver
            ? "scale-[1.01] border-blue-400 bg-blue-50/50"
            : error
              ? "border-red-300 bg-red-50/30"
              : file
                ? "border-emerald-300 bg-emerald-50/20"
                : "border-neutral-200 hover:border-neutral-300 hover:bg-neutral-50"
        } `}
        onClick={() => inputRef.current?.click()}
        onDrop={onDrop}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={(e) => {
          e.preventDefault();
          setDragOver(false);
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          className="hidden"
          onChange={onChange}
        />

        {previewUrl ? (
          /* preview mode */
          <div className="flex flex-col items-center gap-4">
            <div className="relative aspect-square w-full max-w-[240px] overflow-hidden rounded-xl border border-black/5 shadow-md">
              <Image src={previewUrl} alt="预览图片" fill className="object-cover" unoptimized />
            </div>
            <div className="flex items-center gap-3">
              <p className="text-[14px] font-medium text-neutral-700">{file?.name}</p>
              <span className="text-[12px] text-neutral-400">
                {file ? (file.size / 1024 / 1024).toFixed(1) : "0"} MB
              </span>
            </div>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onFileRemove();
              }}
              className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[13px] font-medium text-red-600 transition-colors hover:bg-red-50"
            >
              <TrashIcon className="h-3.5 w-3.5" />
              移除图片
            </button>
          </div>
        ) : (
          /* empty state */
          <div className="space-y-4">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-neutral-100">
              <ImageIcon className="h-8 w-8 text-neutral-400" />
            </div>
            <div>
              <p className="text-[15px] font-medium text-neutral-800">拖拽图片到此处上传</p>
              <p className="mt-1.5 text-[13px] text-neutral-400">
                或点击选择文件 · JPG / PNG / WebP · 最大 10 MB
              </p>
            </div>
          </div>
        )}
      </div>

      {/* error message */}
      {error && (
        <div className="animate-fade-in flex items-center gap-2 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-[13px] text-red-600">
          <svg
            className="h-4 w-4 shrink-0"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{error}</span>
          <button
            onClick={() => setError(null)}
            className="ml-auto text-red-400 hover:text-red-600"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}
