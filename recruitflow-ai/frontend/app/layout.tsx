import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "RecruitFlow AI",
  description: "招聘流程智能助手"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
