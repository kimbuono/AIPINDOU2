import type { Metadata, Viewport } from "next";
import { Geist } from "next/font/google";
import "./globals.css";

const geist = Geist({
  subsets: ["latin"],
  variable: "--font-geist-sans",
});

export const metadata: Metadata = {
  title: {
    default: "爱拼豆 — 拼豆图纸生成器",
    template: "%s · 爱拼豆",
  },
  description:
    "上传照片，自动生成专业拼豆图纸。支持多种尺寸与颜色，包含网格、图例与数量统计，免费在线使用。",
  keywords: [
    "拼豆", "拼豆图纸", "perler beads", "hama beads", "bead art",
    "图纸生成器", "拼豆图案", "像素画", "拼豆设计",
  ],
  authors: [{ name: "爱拼豆" }],
  robots: "index, follow",
  openGraph: {
    title: "爱拼豆 — 拼豆图纸生成器",
    description: "上传照片，自动生成专业拼豆图纸。",
    type: "website",
    locale: "zh_CN",
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN" className={`${geist.variable} antialiased`}>
      <body className="min-h-screen flex flex-col">{children}</body>
    </html>
  );
}
