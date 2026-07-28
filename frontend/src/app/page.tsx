"use client";

import { useState, useEffect } from "react";
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
type ColorCount = 16 | 24 | 32 | 48 | 64 | 80 | 96 | 128 | 256;
type Brand = "artkal" | "perler";

interface BlueprintStats {
  codes: string[];
  names: string[];
  rgb: [number, number, number][];
  counts: number[];
  total: number;
  grid_size: number;
  n_colors: number;
  brand: string;
}

type AppState = "idle" | "ready" | "generating" | "done" | "error";

const API_URL =
  typeof window !== "undefined"
    ? process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
    : "http://localhost:8000";

// ── warm-up: ping backend on page load to wake it from Render sleep ──
function warmUpBackend() {
  const ctrl = new AbortController();
  setTimeout(() => ctrl.abort(), 5000);
  fetch(`${API_URL}/api/health`, { method: "GET", signal: ctrl.signal })
    .then(r => r.json().catch(() => ({})))
    .then(d => { if (d.version) console.log("[爱拼豆] 后端就绪 v" + d.version); })
    .catch(() => { /* silent */ });
}

// ── page ───────────────────────────────────────────────────────────────

export default function Home() {
  // file
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // config
  const [gridSize, setGridSize] = useState<GridSize>(48);
  const [colorCount, setColorCount] = useState<ColorCount>(32);
  const [brand, setBrand] = useState<Brand>("artkal");

  // result
  const [appState, setAppState] = useState<AppState>("idle");
  const [blueprintUrl, setBlueprintUrl] = useState<string | null>(null);
  const [stats, setStats] = useState<BlueprintStats | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isLanding = appState === "idle" || appState === "ready";

  // ── warm up backend on first visit ──────────────────────────────
  useEffect(() => { warmUpBackend(); }, []);

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
      fd.append("brand", brand);

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60_000);

      const res = await fetch(`${API_URL}/api/generate?format=json`, {
        method: "POST",
        body: fd,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!res.ok) {
        const body = await res.json().catch(() => ({})) as { detail?: string };
        throw new Error(body.detail || `服务器错误（${res.status}）`);
      }

      const data = await res.json();
      const imgBlob = base64ToBlob(data.image_base64, "image/png");
      setBlueprintUrl(URL.createObjectURL(imgBlob));
      setStats({
        codes: data.codes,
        names: data.names,
        rgb: data.rgb,
        counts: data.counts,
        total: data.total,
        grid_size: data.grid_size,
        n_colors: data.n_colors,
        brand: data.brand,
      });
      setAppState("done");
    } catch (err) {
      const isTimeout = (err as Error).name === "AbortError";
      setErrorMessage(
        isTimeout
          ? "请求超时，请检查网络后重试"
          : "网络连接失败，请检查网络后重试"
      );
      setAppState("error");
    }
  };

  const handleDownload = () => {
    if (!blueprintUrl) return;
    const a = document.createElement("a");
    a.href = blueprintUrl;
    a.download = `爱拼豆_${brand}_${gridSize}x${gridSize}.png`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  // ── render ───────────────────────────────────────────────────────

  return (
    <div className="flex flex-col min-h-screen bg-[#fafafa]">
      <Header />

      <main className="flex-1">
        {appState === "idle" && <Hero />}

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

          {/* config */}
          {file && appState !== "done" && (
            <section className="animate-fade-in">
              <ConfigPanel
                gridSize={gridSize}
                colorCount={colorCount}
                brand={brand}
                onGridSizeChange={setGridSize}
                onColorCountChange={setColorCount}
                onBrandChange={setBrand}
              />
            </section>
          )}

          {/* generate */}
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
            <BlueprintResult
              imageUrl={blueprintUrl}
              stats={stats}
              originalUrl={previewUrl}
              onDownload={handleDownload}
              onRegenerate={handleGenerate}
              onReset={handleFileRemove}
            />
          )}
        </div>

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
