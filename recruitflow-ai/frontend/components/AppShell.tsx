"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, ClipboardCheck, FileUp, Inbox, ListTodo, Settings, Table2, Users } from "lucide-react";

const navItems = [
  { href: "/", label: "Dashboard", icon: BarChart3 },
  { href: "/upload", label: "AI 简历录入", icon: FileUp },
  { href: "/pending", label: "待确认简历", icon: Inbox },
  { href: "/candidates", label: "候选人", icon: Users },
  { href: "/tasks", label: "智能待办", icon: ListTodo },
  { href: "/events", label: "事件日志", icon: ClipboardCheck },
  { href: "/settings", label: "系统设置", icon: Settings },
  { href: "/candidates?view=kanban", label: "看板视图", icon: Table2 }
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  return (
    <div className="min-h-screen bg-[#f6f8fb]">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-line bg-white px-4 py-5 lg:block">
        <div className="mb-8">
          <p className="text-sm font-semibold text-brand">RecruitFlow AI</p>
          <h1 className="mt-1 text-xl font-semibold text-ink">招聘流程智能助手</h1>
        </div>
        <nav className="space-y-1">
          {navItems.map((item) => {
            const active = pathname === item.href.split("?")[0];
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm ${
                  active ? "bg-blue-50 text-brand" : "text-slate-600 hover:bg-slate-50"
                }`}
              >
                <Icon size={18} />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <div className="lg:pl-64">
        <header className="border-b border-line bg-white px-5 py-4 lg:px-8">
          <p className="text-sm text-muted">非侵入式 Demo：从 HR 主动下载或上传简历开始，不登录、不抓取 BOSS。</p>
        </header>
        <main className="px-5 py-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}
