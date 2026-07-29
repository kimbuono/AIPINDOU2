"use client";

import { useState, useEffect } from "react";
import { getUser, type User } from "@/components/AuthModal";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Project {
  id: number;
  name: string;
  grid_size: number;
  n_colors: number;
  brand: string;
  is_favorite: number;
  created_at: string;
  updated_at: string;
  blueprint_image: string | null;
}

export default function ProjectsPage() {
  const [user, setUser] = useState<User | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    const { user: u } = getUser();
    setUser(u);
  }, []);

  useEffect(() => {
    if (!user) { setLoading(false); return; }
    loadProjects();
  }, [user, search]);

  const loadProjects = async () => {
    const { token } = getUser();
    if (!token) {
      setLoading(false);
      return;
    }
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15_000);
    try {
      const url = `${API_URL}/api/projects?sort=updated_at${search ? `&search=${encodeURIComponent(search)}` : ""}`;
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
        signal: controller.signal,
      });
      if (res.ok) setProjects(await res.json());
    } catch {
      setError("服务器连接失败，请刷新重试");
    } finally {
      clearTimeout(timeoutId);
      setLoading(false);
    }
  };

  const deleteProject = async (id: number) => {
    const { token } = getUser();
    if (!token || !confirm("确定删除这个项目？")) return;
    await fetch(`${API_URL}/api/projects/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    setProjects(p => p.filter(p => p.id !== id));
  };

  const toggleFavorite = async (p: Project) => {
    const { token } = getUser();
    if (!token) return;
    const res = await fetch(`${API_URL}/api/projects/${p.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        name: p.name, grid_size: p.grid_size, n_colors: p.n_colors,
        brand: p.brand, is_favorite: !p.is_favorite, is_public: false,
      }),
    });
    if (res.ok) {
      setProjects(prev => prev.map(proj =>
        proj.id === p.id ? { ...proj, is_favorite: !p.is_favorite ? 1 : 0 } : proj
      ));
    }
  };

  if (!user) {
    return (
      <div className="flex flex-col min-h-screen bg-[#fafafa]">
        <Header onOpenAuth={() => {}} />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <p className="text-[15px] text-neutral-500 mb-3">请先登录查看作品</p>
            <Link href="/" className="text-[14px] text-blue-500 font-medium">返回首页</Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="flex flex-col min-h-screen bg-[#fafafa]">
      <Header onOpenAuth={() => {}} />
      <main className="flex-1 mx-auto w-full max-w-4xl px-5 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-[20px] font-bold text-neutral-800">我的作品</h1>
          <Link href="/" className="text-[14px] font-medium text-blue-500">+ 新建图纸</Link>
        </div>

        {/* search */}
        <input
          className="w-full mb-6 px-4 py-2.5 rounded-xl border border-neutral-200 text-[14px] outline-none focus:border-neutral-400"
          placeholder="搜索项目…"
          value={search}
          onChange={e => setSearch(e.target.value)}
        />

        {loading ? (
          <p className="text-center text-neutral-400 py-12">加载中…</p>
        ) : projects.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-[15px] text-neutral-400 mb-3">还没有保存的作品</p>
            <Link href="/" className="text-[14px] font-medium text-blue-500">去创建第一个图纸 →</Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map(p => (
              <div key={p.id} className="bg-white rounded-2xl border border-neutral-200 overflow-hidden hover:shadow-sm transition-shadow">
                {/* thumbnail */}
                <div className="aspect-square bg-neutral-100 flex items-center justify-center">
                  {p.blueprint_image ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={`data:image/png;base64,${p.blueprint_image}`} alt={p.name} className="w-full h-full object-contain p-2" />
                  ) : (
                    <span className="text-neutral-300 text-[13px]">无预览</span>
                  )}
                </div>
                {/* info */}
                <div className="p-4">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="text-[14px] font-semibold text-neutral-800 truncate">{p.name}</h3>
                    <button onClick={() => toggleFavorite(p)} className="text-lg">
                      {p.is_favorite ? "★" : "☆"}
                    </button>
                  </div>
                  <p className="text-[12px] text-neutral-400">
                    {p.grid_size}×{p.grid_size} · {p.n_colors}色 · {p.brand.toUpperCase()}
                  </p>
                  <p className="text-[11px] text-neutral-300 mt-1">
                    {new Date(p.updated_at).toLocaleDateString("zh-CN")}
                  </p>
                  <div className="flex gap-2 mt-3">
                    <Link
                      href={`/?load=${p.id}`}
                      className="flex-1 text-center py-1.5 rounded-lg bg-neutral-100 text-[13px] font-medium text-neutral-600 hover:bg-neutral-200"
                    >
                      打开
                    </Link>
                    <button
                      onClick={() => deleteProject(p.id)}
                      className="px-3 py-1.5 rounded-lg text-[13px] text-red-500 hover:bg-red-50"
                    >
                      删除
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
      <Footer />
    </div>
  );
}
