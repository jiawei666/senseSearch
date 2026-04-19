import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SenseSearch - 智能内容搜索",
  description: "基于 AI 的多媒体内容搜索平台，支持文本、图片和视频搜索",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className="h-full antialiased">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
