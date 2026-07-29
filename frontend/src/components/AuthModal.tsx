"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface User {
  id: number;
  email: string;
  username: string;
}

interface AuthModalProps {
  open: boolean;
  onClose: () => void;
  onLogin: (user: User, token: string) => void;
}

export type { User };

export function getUser(): { user: User | null; token: string | null } {
  if (typeof window === "undefined") return { user: null, token: null };
  try {
    const u = localStorage.getItem("aipindou_user");
    const t = localStorage.getItem("aipindou_token");
    return { user: u ? JSON.parse(u) : null, token: t };
  } catch {
    return { user: null, token: null };
  }
}

export function saveAuth(user: User, token: string) {
  localStorage.setItem("aipindou_user", JSON.stringify(user));
  localStorage.setItem("aipindou_token", token);
}

export function clearAuth() {
  localStorage.removeItem("aipindou_user");
  localStorage.removeItem("aipindou_token");
}

export default function AuthModal({ open, onClose, onLogin }: AuthModalProps) {
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  if (!open) return null;

  const submit = async () => {
    setError("");
    setLoading(true);
    try {
      const endpoint = mode === "login" ? "/api/auth/login" : "/api/auth/signup";
      const body = mode === "login"
        ? { email, password }
        : { email, username, password };

      const res = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "请求失败");

      saveAuth(data.user, data.token);
      onLogin(data.user, data.token);
      onClose();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-xl border border-neutral-200 w-full max-w-sm mx-4 p-6" onClick={e => e.stopPropagation()}>
        <h2 className="text-[17px] font-bold text-neutral-800 mb-5">
          {mode === "login" ? "登录" : "注册"}
        </h2>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-100 text-[13px] text-red-600">{error}</div>
        )}

        <div className="space-y-3">
          <input
            className="w-full px-3.5 py-2.5 rounded-xl border border-neutral-200 text-[14px] outline-none focus:border-neutral-400"
            placeholder="邮箱"
            type="email"
            value={email}
            onChange={e => setEmail(e.target.value)}
            onKeyDown={e => e.key === "Enter" && submit()}
          />
          {mode === "signup" && (
            <input
              className="w-full px-3.5 py-2.5 rounded-xl border border-neutral-200 text-[14px] outline-none focus:border-neutral-400"
              placeholder="用户名"
              value={username}
              onChange={e => setUsername(e.target.value)}
              onKeyDown={e => e.key === "Enter" && submit()}
            />
          )}
          <input
            className="w-full px-3.5 py-2.5 rounded-xl border border-neutral-200 text-[14px] outline-none focus:border-neutral-400"
            placeholder="密码"
            type="password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            onKeyDown={e => e.key === "Enter" && submit()}
          />
        </div>

        <button
          onClick={submit}
          disabled={loading || !email || !password}
          className="w-full mt-4 py-2.5 rounded-xl bg-neutral-900 text-white text-[14px] font-semibold disabled:opacity-30"
        >
          {loading ? "请稍候…" : mode === "login" ? "登录" : "注册"}
        </button>

        <p className="mt-4 text-center text-[13px] text-neutral-400">
          {mode === "login" ? "还没有账号？" : "已有账号？"}
          <button className="ml-1 text-neutral-800 font-medium" onClick={() => { setMode(mode === "login" ? "signup" : "login"); setError(""); }}>
            {mode === "login" ? "注册" : "登录"}
          </button>
        </p>
      </div>
    </div>
  );
}
