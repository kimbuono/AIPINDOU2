"use client";

import { useState } from "react";
import Header from "@/components/Header";
import Hero from "@/components/Hero";
import UploadZone from "@/components/UploadZone";
import ConfigPanel from "@/components/ConfigPanel";
import GenerateButton from "@/components/GenerateButton";
import BlueprintResult from "@/components/BlueprintResult";
import FeatureCards from "@/components/FeatureCards";
import HowItWorks from "@/components/HowItWorks";
import Footer from "@/components/Footer";
import { AlertIcon } from "@/components/Icons";

// ── types ──────────────────────────────────────────────────────────────
type GridSize = 16 | 29 | 32 | 48 | 58 | 64;
type ColorCount = 16 | 24 | 32 | 48;

interface BlueprintStats {
  palette: [number, number, number][];
  counts: number[];
  total: number;
  grid_size: number;
  n_colors: number;
}

type AppState = "idle" | "ready" | "generating" | "done" | "error";

const API_URL =
  typeof window !== "undefined"
    ? process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
    : "http://localhost:8000";

// ── page ───────────────────────────────────────────────────────────────

export default function Home() {
  // file state
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // config state
  const [gridSize, setGridSize] = useState<GridSize>(48);
  const [colorCount, setColorCount] = useState<ColorCount>(32);

  // result state
  const [appState, setAppState] = useState<AppState>("idle");
  const [blueprintUrl, setBlueprintUrl] = useState<string | null>(null);
  const [stats, setStats] = useState<BlueprintStats | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // derived
  const isLanding = appState === "idle" || appState === "ready";

  // ── handlers ─────────────────────────────────────────────────────

  const handleFileAccepted = (f: File) => {
    setFile(f);
    setPreviewUrl(URL.createObjectURL(f));
    setAppState("ready");
    setBlueprintUrl(null);
    setStats(null);
    setErrorMessage(null);
  };

  const handleFileRemove = () => {
    setFile(null);
    setPreviewUrl(null);
    setAppState("idle");
    setBlueprintUrl(null);
    setStats(null);
    setErrorMessage(null);
  };

  const handleGenerate = async () => {
    if (!file) return;
    setAppState("generating");
    setErrorMessage(null);
    setBlueprintUrl(null);
    setStats(null);

    try {
      const fd = new FormData();
      fd.append("image", file);
      fd.append("size", String(gridSize));
      fd.append("colors", String(colorCount));

      const res = await fetch(`${API_URL}/api/generate?format=json`, {
        method: "POST",
        body: fd,
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({})) as { detail?: string };
        throw new Error(body.detail || `服务器错误（${res.status}）`);
      }

      const data = await res.json();
      const imgBlob = base64ToBlob(data.image_base64, "image/png");
      setBlueprintUrl(URL.createObjectURL(imgBlob));
      setStats({
        palette: data.palette,
        counts: data.counts,
        total: data.total,
        grid_size: data.grid_size,
        n_colors: data.n_colors,
      });
      setAppState("done");
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "生成失败，请重试");
      setAppState("error");
    }
  };

  const handleDownload = () => {
    if (!blueprintUrl) return;
    const a = document.createElement("a");
    a.href = blueprintUrl;
    a.download = `爱拼豆_${gridSize}x${gridSize}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  // ── render ───────────────────────────────────────────────────────

  return (
    <div className="flex flex-col min-h-screen bg-[#fafafa]">
      <Header />

      <main className="flex-1">
        {/* hero — only when landing (no file) */}
        {appState === "idle" && <Hero />}

        {/* workspace */}
        <div className="mx-auto max-w-2xl px-5 pb-20 space-y-6">
          {/* upload */}
          <section className={appState === "idle" ? "-mt-6" : "mt-8"}>
            <UploadZone
              file={file}
              previewUrl={previewUrl}
              onFileAccepted={handleFileAccepted}
              onFileRemove={handleFileRemove}
            />
          </section>

          {/* config — only after image uploaded, before result */}
          {file && appState !== "done" && (
            <section className="animate-fade-in">
              <ConfigPanel
                gridSize={gridSize}
                colorCount={colorCount}
                onGridSizeChange={setGridSize}
                onColorCountChange={setColorCount}
              />
            </section>
          )}

          {/* generate CTA */}
          {file && appState !== "done" && (
            <section className={appState === "ready" ? "animate-fade-in" : ""}>
              <GenerateButton
                disabled={!file}
                loading={appState === "generating"}
                onClick={handleGenerate}
              />
            </section>
          )}

          {/* error */}
          {appState === "error" && errorMessage && (
            <section className="animate-fade-in">
              <div className="flex items-start gap-3 px-5 py-4 rounded-2xl bg-red-50 border border-red-100">
                <AlertIcon className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="text-[14px] font-semibold text-red-700">生成失败</p>
                  <p className="text-[13px] text-red-600/70 mt-0.5">{errorMessage}</p>
                </div>
                <button
                  onClick={() => { setAppState("ready"); setErrorMessage(null); }}
                  className="shrink-0 text-[13px] font-medium text-red-600 hover:text-red-800 transition-colors"
                >
                  重试
                </button>
              </div>
            </section>
          )}

          {/* result */}
          {appState === "done" && stats && blueprintUrl && (
            <section>
              <BlueprintResult
                imageUrl={blueprintUrl}
                stats={stats}
                originalUrl={previewUrl}
                onDownload={handleDownload}
              />

              {/* regenerate / reset */}
              <div className="flex items-center gap-3 mt-6">
                <button
                  onClick={handleGenerate}
                  className="flex-1 py-3 rounded-xl text-[14px] font-semibold border border-neutral-200
                             text-neutral-600 hover:bg-neutral-50 transition-colors"
                >
                  重新生成
                </button>
                <button
                  onClick={handleFileRemove}
                  className="flex-1 py-3 rounded-xl text-[14px] font-semibold border border-neutral-200
                             text-neutral-600 hover:bg-neutral-50 transition-colors"
                >
                  制作新图纸
                </button>
              </div>
            </section>
          )}
        </div>

        {/* landing sections — only when no file */}
        {isLanding && (
          <>
            <FeatureCards />
            <HowItWorks />
          </>
        )}
      </main>

      <Footer />
    </div>
  );
}

// ── helpers ────────────────────────────────────────────────────────────

function base64ToBlob(b64: string, mime: string): Blob {
  const bytes = atob(b64);
  const buf = new ArrayBuffer(bytes.length);
  const arr = new Uint8Array(buf);
  for (let i = 0; i < bytes.length; i++) {
    arr[i] = bytes.charCodeAt(i);
  }
  return new Blob([buf], { type: mime });
}
