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
import AuthModal, { getUser, saveAuth, type User } from "@/components/AuthModal";

// ── types ──────────────────────────────────────────────────────────────
type GridSize = 16 | 29 | 32 | 48 | 58 | 64;
type ColorCount = 8 | 16 | 24 | 32 | 48 | 64 | 96 | 128 | 192 | 256;
type Brand = "artkal" | "perler" | "hama";

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
    .then((r) => r.json().catch(() => ({})))
    .then((d) => {
      if (d.version) console.log("[爱拼豆] 后端就绪 v" + d.version);
    })
    .catch(() => {
      /* silent */
    });
}

// ── page ───────────────────────────────────────────────────────────────

export default function Home() {
  // file
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  // config
  const [gridSize, setGridSize] = useState<GridSize>(48);
  const [colorCount, setColorCount] = useState<ColorCount>(48);
  const [brand, setBrand] = useState<Brand>("artkal");
  const [dither, setDither] = useState(true);

  // result
  const [appState, setAppState] = useState<AppState>("idle");
  const [blueprintUrl, setBlueprintUrl] = useState<string | null>(null);
  const [stats, setStats] = useState<BlueprintStats | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isLanding = appState === "idle" || appState === "ready";

  // ── auth state ──────────────────────────────────────────────────
  const [authOpen, setAuthOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [saveStatus, setSaveStatus] = useState<"" | "saving" | "saved" | "error">("");

  useEffect(() => {
    warmUpBackend();
  }, []);
  useEffect(() => {
    const { user: u } = getUser();
    setCurrentUser(u);
    // Load project if ?load=<id> in URL
    const params = new URLSearchParams(window.location.search);
    const loadId = params.get("load");
    if (loadId && u) loadProject(parseInt(loadId));
  }, []);

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
      fd.append("dither", dither ? "true" : "false");

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120_000);

      let res: Response;
      try {
        res = await fetch(`${API_URL}/api/generate?format=json`, {
          method: "POST",
          body: fd,
          signal: controller.signal,
        });
      } catch (fetchErr: unknown) {
        clearTimeout(timeoutId);
        if ((fetchErr as Error).name === "AbortError") {
          throw new Error("TIMEOUT");
        }
        // Network error (DNS, CORS, connection refused)
        throw new Error("NETWORK:" + ((fetchErr as Error).message || "无法连接到服务器"));
      }
      clearTimeout(timeoutId);

      if (!res.ok) {
        let detail = "";
        try {
          const body = (await res.json()) as { detail?: string };
          detail = body.detail || "";
        } catch {
          // ignore parse errors on error response
        }
        throw new Error("SERVER:" + (detail || `服务器错误 HTTP ${res.status}`));
      }

      let data: {
        image_base64: string;
        codes: string[];
        names: string[];
        rgb: [number, number, number][];
        counts: number[];
        total: number;
        grid_size: number;
        n_colors: number;
        brand: string;
      };
      try {
        data = await res.json();
      } catch {
        throw new Error("SERVER:返回数据格式异常，请重试");
      }

      if (!data.image_base64 || !data.rgb || !data.counts) {
        throw new Error("SERVER:返回数据不完整，请重试");
      }

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
      const msg = (err as Error).message || "";
      if (msg.startsWith("TIMEOUT")) {
        setErrorMessage("请求超时。服务器可能正在启动，请等待 30 秒后点击「重新生成」");
      } else if (msg.startsWith("SERVER:")) {
        setErrorMessage(msg.slice(7));
      } else if (msg.startsWith("NETWORK:")) {
        setErrorMessage(msg.slice(8));
      } else {
        setErrorMessage(msg || "未知错误，请重试");
      }
      setAppState("error");
    }
  };

  const saveProject = async () => {
    if (!currentUser || !blueprintUrl || !stats) return;
    const { token } = getUser();
    if (!token) {
      setSaveStatus("error");
      return;
    }
    setSaveStatus("saving");
    try {
      const ctrl = new AbortController();
      const tid = setTimeout(() => ctrl.abort(), 30_000);
      const blob = await fetch(blueprintUrl, { signal: ctrl.signal }).then((r) => r.blob());
      clearTimeout(tid);
      const reader = new FileReader();
      const bpBase64 = await new Promise<string>((resolve) => {
        reader.onload = () => resolve((reader.result as string).split(",")[1]);
        reader.readAsDataURL(blob);
      });

      const ctrl2 = new AbortController();
      const tid2 = setTimeout(() => ctrl2.abort(), 15_000);
      const res = await fetch(`${API_URL}/api/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          name: `拼豆图纸 ${gridSize}×${gridSize}`,
          grid_size: gridSize,
          n_colors: colorCount,
          brand,
          dither,
          blueprint_image: bpBase64,
          stats_json: JSON.stringify(stats),
        }),
        signal: ctrl2.signal,
      });
      clearTimeout(tid2);
      if (res.ok) setSaveStatus("saved");
      else setSaveStatus("error");
    } catch {
      setSaveStatus("error");
    }
  };

  const loadProject = async (id: number) => {
    const { token } = getUser();
    if (!token) return;
    const ctrl = new AbortController();
    const tid = setTimeout(() => ctrl.abort(), 15_000);
    try {
      const res = await fetch(`${API_URL}/api/projects/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
        signal: ctrl.signal,
      });
      clearTimeout(tid);
      if (!res.ok) return;
      const p = await res.json();
      // Restore config
      setGridSize(p.grid_size);
      if ([16, 24, 32, 48, 64, 80, 96, 128, 256].includes(p.n_colors)) {
        setColorCount(p.n_colors as ColorCount);
      }
      if (["artkal", "perler"].includes(p.brand)) setBrand(p.brand as Brand);
      setDither(!!p.dither);
      // Restore blueprint
      if (p.blueprint_image) {
        const blob = base64ToBlob(p.blueprint_image, "image/png");
        setBlueprintUrl(URL.createObjectURL(blob));
        if (p.stats_json) {
          try {
            setStats(JSON.parse(p.stats_json));
          } catch {
            /* ignore */
          }
        }
        setAppState("done");
      }
    } catch {
      /* silent */
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
    <div className="flex min-h-screen flex-col bg-[#fafafa]">
      <Header onOpenAuth={() => setAuthOpen(true)} />
      <AuthModal
        open={authOpen}
        onClose={() => setAuthOpen(false)}
        onLogin={(user) => {
          setCurrentUser(user);
          (window as unknown as Record<string, () => void>).__refreshHeaderUser?.();
        }}
      />

      <main className="flex-1">
        {appState === "idle" && <Hero />}

        <div className="mx-auto max-w-2xl space-y-6 px-5 pb-20">
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
                dither={dither}
                onGridSizeChange={setGridSize}
                onColorCountChange={setColorCount}
                onBrandChange={setBrand}
                onDitherChange={setDither}
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
              <div className="flex items-start gap-3 rounded-2xl border border-red-100 bg-red-50 px-5 py-4">
                <AlertIcon className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
                <div className="min-w-0 flex-1">
                  <p className="text-[14px] font-semibold text-red-700">生成失败</p>
                  <p className="mt-0.5 text-[13px] text-red-600/70">{errorMessage}</p>
                </div>
                <button
                  onClick={() => {
                    setAppState("ready");
                    setErrorMessage(null);
                  }}
                  className="shrink-0 text-[13px] font-medium text-red-600 transition-colors hover:text-red-800"
                >
                  重试
                </button>
              </div>
            </section>
          )}

          {/* result */}
          {appState === "done" && stats && blueprintUrl && (
            <>
              <BlueprintResult
                imageUrl={blueprintUrl}
                stats={stats}
                originalUrl={previewUrl}
                onDownload={handleDownload}
                onRegenerate={handleGenerate}
                onReset={handleFileRemove}
              />
              {/* Save button */}
              {currentUser && (
                <div className="mt-3 flex items-center gap-3">
                  <button
                    onClick={saveProject}
                    disabled={saveStatus === "saving"}
                    className="flex-1 rounded-xl bg-emerald-600 py-3 text-[14px] font-semibold text-white transition-colors hover:bg-emerald-700 disabled:opacity-50"
                  >
                    {saveStatus === "saving"
                      ? "正在保存…"
                      : saveStatus === "saved"
                        ? "已保存 ✓"
                        : "保存到我的作品"}
                  </button>
                  {saveStatus === "error" && (
                    <span className="text-[13px] text-red-500">保存失败</span>
                  )}
                </div>
              )}
              {!currentUser && (
                <p className="mt-3 text-center text-[13px] text-neutral-400">
                  <button onClick={() => setAuthOpen(true)} className="font-medium text-blue-500">
                    登录
                  </button>
                  后可以保存作品
                </p>
              )}
            </>
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
