"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { BarChart3, BriefcaseBusiness, ClipboardCheck, FileUp, Inbox, ListTodo, LogIn, LogOut, Settings, Table2, Users } from "lucide-react";
import { AuthModal } from "@/components/AuthModal";
import { clearSession, getSession, type AuthSession } from "@/lib/api";

type Role = AuthSession["role"];

const navItems: Array<{ href: string; label: string; icon: typeof BarChart3; roles: Role[] }> = [
  { href: "/", label: "Dashboard", icon: BarChart3, roles: ["hr", "department"] },
  { href: "/upload", label: "AI 简历录入", icon: FileUp, roles: ["hr"] },
  { href: "/pending", label: "待确认简历", icon: Inbox, roles: ["hr"] },
  { href: "/candidates", label: "候选人", icon: Users, roles: ["hr", "department"] },
  { href: "/jobs", label: "JD 与 AI 二筛", icon: BriefcaseBusiness, roles: ["department"] },
  { href: "/tasks", label: "智能待办", icon: ListTodo, roles: ["hr", "department"] },
  { href: "/events", label: "事件日志", icon: ClipboardCheck, roles: ["hr", "department"] },
  { href: "/settings", label: "系统设置", icon: Settings, roles: ["hr", "department"] },
  { href: "/candidates?view=kanban", label: "看板视图", icon: Table2, roles: ["hr", "department"] },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [session, setSession] = useState<AuthSession | null>(null);
  const [sessionLoaded, setSessionLoaded] = useState(false);
  const [loginOpen, setLoginOpen] = useState(false);

  useEffect(() => {
    const loadSession = window.setTimeout(() => {
      const stored = getSession();
      setSession(stored);
      setSessionLoaded(true);
      setLoginOpen(stored === null);
    }, 0);
    const handleUnauthorized = () => {
      setSession(null);
      setLoginOpen(true);
    };
    window.addEventListener("recruitflow:unauthorized", handleUnauthorized);
    return () => {
      window.clearTimeout(loadSession);
      window.removeEventListener("recruitflow:unauthorized", handleUnauthorized);
    };
  }, []);

  const visibleNavItems = useMemo(
    () => (session ? navItems.filter((item) => item.roles.includes(session.role)) : []),
    [session],
  );

  function logout() {
    clearSession();
    setSession(null);
    setLoginOpen(true);
  }

  return (
    <div className="min-h-screen bg-[#f6f8fb]">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-line bg-white px-4 py-5 lg:block">
        <div className="mb-8">
          <p className="text-sm font-semibold text-brand">RecruitFlow AI</p>
          <h1 className="mt-1 text-xl font-semibold text-ink">招聘流程智能助手</h1>
        </div>
        <nav className="space-y-1">
          {visibleNavItems.map((item) => {
            const active = pathname === item.href.split("?")[0];
            const Icon = item.icon;
            return (
              <Link key={item.href} href={item.href} className={`flex items-center gap-3 rounded-md px-3 py-2 text-sm ${active ? "bg-blue-50 text-brand" : "text-slate-600 hover:bg-slate-50"}`}>
                <Icon size={18} />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>
      <div className="lg:pl-64">
        <header className="flex items-center justify-between gap-4 border-b border-line bg-white px-5 py-3 lg:px-8">
          <p className="text-sm text-muted">非侵入式 Demo：由 HR 上传简历，AI 二筛只给建议，人工确认后才改变阶段。</p>
          <div className="flex shrink-0 items-center gap-2">
            {session ? (
              <>
                <button className="rounded-md border border-line px-3 py-2 text-left text-xs hover:bg-slate-50" onClick={() => setLoginOpen(true)}>
                  <span className="block font-medium text-ink">{session.displayName}</span>
                  <span className="text-muted">{session.role === "hr" ? "HR 权限" : "用人部门权限"}</span>
                </button>
                <button className="rounded-md border border-line p-2 text-slate-600 hover:bg-slate-50" onClick={logout} aria-label="退出登录"><LogOut size={18} /></button>
              </>
            ) : (
              <button className="flex items-center gap-2 rounded-md bg-brand px-3 py-2 text-sm text-white" onClick={() => setLoginOpen(true)}><LogIn size={17} />角色登录</button>
            )}
          </div>
        </header>
        <main className="px-5 py-6 lg:px-8">{children}</main>
      </div>
      {sessionLoaded ? <AuthModal open={loginOpen} onClose={() => setLoginOpen(false)} onAuthenticated={setSession} /> : null}
    </div>
  );
}
