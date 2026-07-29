"use client";

import Link from "next/link";
import { getUser, clearAuth, type User } from "./AuthModal";
import { useState, useEffect } from "react";

interface HeaderProps {
  onOpenAuth: () => void;
}

export default function Header({ onOpenAuth }: HeaderProps) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const { user: u } = getUser();
    setUser(u);
  }, []);

  const refreshUser = () => {
    const { user: u } = getUser();
    setUser(u);
  };

  // Expose refreshUser globally so page.tsx can call it
  if (typeof window !== "undefined") {
    (window as unknown as Record<string, unknown>).__refreshHeaderUser = refreshUser;
  }

  return (
    <header className="sticky top-0 z-40 border-b border-black/5 bg-white/80 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-5">
        <Link href="/" className="flex items-center gap-2.5 select-none">
          <span className="text-[26px] leading-none">🫘</span>
          <span className="text-[17px] font-semibold tracking-tight text-neutral-900">爱拼豆</span>
        </Link>

        <div className="flex items-center gap-3">
          {user ? (
            <>
              <Link
                href="/projects"
                className="text-[13px] font-medium text-neutral-500 transition-colors hover:text-neutral-800"
              >
                我的作品
              </Link>
              <span className="hidden text-[13px] text-neutral-400 sm:inline">{user.username}</span>
              <button
                onClick={() => {
                  clearAuth();
                  setUser(null);
                }}
                className="text-[13px] text-neutral-400 transition-colors hover:text-red-500"
              >
                退出
              </button>
            </>
          ) : (
            <button
              onClick={onOpenAuth}
              className="rounded-lg bg-neutral-900 px-4 py-1.5 text-[13px] font-medium text-white transition-colors hover:bg-neutral-800"
            >
              登录
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
