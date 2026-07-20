"use client";

import { FormEvent, useState } from "react";
import { X } from "lucide-react";
import { apiPost, saveSession, type AuthSession } from "@/lib/api";

type LoginResult = { access_token: string; role: "hr" | "department"; display_name: string };

type AuthModalProps = {
  open: boolean;
  onClose: () => void;
  onAuthenticated: (session: AuthSession) => void;
};

const demoAccounts = {
  department: { username: "department_demo", password: "department-demo-2026", displayName: "李审批" },
  hr: { username: "hr_demo", password: "hr-demo-2026", displayName: "张招聘" },
} as const;

export function AuthModal({ open, onClose, onAuthenticated }: AuthModalProps) {
  const [account, setAccount] = useState<keyof typeof demoAccounts>("department");
  const [username, setUsername] = useState<string>(demoAccounts.department.username);
  const [password, setPassword] = useState<string>(demoAccounts.department.password);
  const [displayName, setDisplayName] = useState<string>(demoAccounts.department.displayName);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (!open) return null;

  function selectAccount(nextAccount: keyof typeof demoAccounts) {
    const selected = demoAccounts[nextAccount];
    setAccount(nextAccount);
    setUsername(selected.username);
    setPassword(selected.password);
    setDisplayName(selected.displayName);
    setError(null);
  }

  async function login(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const result = await apiPost<LoginResult>("/api/auth/login", { username, password, display_name: displayName.trim() });
      saveSession(result.access_token, result.role, result.display_name);
      onAuthenticated({ token: result.access_token, role: result.role, displayName: result.display_name });
      onClose();
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/45 px-4" role="presentation">
      <div className="w-full max-w-md rounded-xl border border-line bg-white p-6 shadow-2xl" role="dialog" aria-modal="true" aria-labelledby="auth-title">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 id="auth-title" className="text-xl font-semibold text-ink">选择演示角色</h2>
            <p className="mt-1 text-sm text-muted">登录成功后立即应用权限并关闭窗口。</p>
          </div>
          <button className="rounded-md p-1 text-slate-500 hover:bg-slate-100" onClick={onClose} aria-label="关闭登录窗口">
            <X size={20} />
          </button>
        </div>

        <div className="mt-5 grid grid-cols-2 gap-2 rounded-lg bg-slate-100 p-1">
          <button className={`rounded-md px-3 py-2 text-sm ${account === "department" ? "bg-white font-medium text-brand shadow-sm" : "text-slate-600"}`} onClick={() => selectAccount("department")}>用人部门</button>
          <button className={`rounded-md px-3 py-2 text-sm ${account === "hr" ? "bg-white font-medium text-brand shadow-sm" : "text-slate-600"}`} onClick={() => selectAccount("hr")}>HR</button>
        </div>

        <form className="mt-5 space-y-4" onSubmit={login}>
          <label className="block text-sm text-ink">
            你的姓名
            <input className="mt-1 w-full rounded-md border border-line px-3 py-2" value={displayName} onChange={(event) => setDisplayName(event.target.value)} autoComplete="name" required minLength={2} />
            <span className="mt-1 block text-xs text-muted">用于审批记录和审计日志，登录后不可由审批请求修改。</span>
          </label>
          <label className="block text-sm text-ink">
            用户名
            <input className="mt-1 w-full rounded-md border border-line px-3 py-2" value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" />
          </label>
          <label className="block text-sm text-ink">
            密码
            <input type="password" className="mt-1 w-full rounded-md border border-line px-3 py-2" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" />
          </label>
          {error ? <p className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p> : null}
          <button disabled={submitting || displayName.trim().length < 2} className="w-full rounded-md bg-brand px-4 py-2.5 text-sm font-medium text-white disabled:opacity-60">
            {submitting ? "正在登录..." : "登录并应用权限"}
          </button>
        </form>
      </div>
    </div>
  );
}
