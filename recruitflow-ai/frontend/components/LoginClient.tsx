"use client";

import { useState } from "react";
import { apiPost, clearSession, saveSession } from "@/lib/api";

type LoginResult = { access_token: string; role: string; display_name: string };

export function LoginClient() {
  const [username, setUsername] = useState("department_demo");
  const [password, setPassword] = useState("department-demo-2026");
  const [displayName, setDisplayName] = useState("李审批");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function login() {
    setError(null);
    try {
      const result = await apiPost<LoginResult>("/api/auth/login", { username, password, display_name: displayName.trim() });
      saveSession(result.access_token, result.role, result.display_name);
      setMessage(`已登录：${result.display_name}（${result.role}）`);
    } catch (reason) {
      setError((reason as Error).message);
    }
  }

  return (
    <div className="mx-auto max-w-lg space-y-5">
      <div>
        <h1 className="text-2xl font-semibold text-ink">角色登录</h1>
        <p className="mt-1 text-sm text-muted">JD 与二筛由用人部门操作，HR 负责简历与招聘流程管理。</p>
      </div>
      <div className="space-y-4 rounded-md border border-line bg-white p-5">
        <label className="block text-sm text-ink">
          姓名
          <input className="mt-1 w-full rounded-md border border-line px-3 py-2" value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
        </label>
        <label className="block text-sm text-ink">
          用户名
          <input className="mt-1 w-full rounded-md border border-line px-3 py-2" value={username} onChange={(event) => setUsername(event.target.value)} />
        </label>
        <label className="block text-sm text-ink">
          密码
          <input type="password" className="mt-1 w-full rounded-md border border-line px-3 py-2" value={password} onChange={(event) => setPassword(event.target.value)} />
        </label>
        <div className="flex gap-2">
          <button className="rounded-md bg-brand px-4 py-2 text-sm text-white" onClick={login}>登录</button>
          <button className="rounded-md border border-line px-4 py-2 text-sm" onClick={() => { clearSession(); setMessage("已退出登录"); }}>退出</button>
        </div>
        <p className="text-xs text-muted">本地 Demo：department_demo / department-demo-2026；hr_demo / hr-demo-2026。部署时必须在环境变量中更换。</p>
        {message ? <p className="text-sm text-emerald-700">{message}</p> : null}
        {error ? <p className="text-sm text-rose-700">{error}</p> : null}
      </div>
    </div>
  );
}
