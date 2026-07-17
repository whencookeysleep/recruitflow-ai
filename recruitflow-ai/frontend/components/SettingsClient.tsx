"use client";

import { useState } from "react";
import { Download, ShieldCheck } from "lucide-react";
import { apiPost } from "@/lib/api";

export function SettingsClient() {
  const [exportResult, setExportResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function exportCsv() {
    setError(null);
    try {
      const result = await apiPost<{ path: string; rows: number; synced_at: string }>("/api/export/csv");
      setExportResult(`已导出 ${result.rows} 条候选人数据：${result.path}`);
    } catch (reason) {
      setError((reason as Error).message);
    }
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold text-ink">系统设置</h1>
        <p className="mt-1 text-sm text-muted">Demo 默认使用 Mock AI、Mock 企业微信和 CSV 模拟腾讯文档同步。</p>
      </div>
      <section className="rounded-md border border-line bg-white p-5">
        <h2 className="flex items-center gap-2 text-base font-semibold text-ink"><ShieldCheck size={18} />安全与隐私</h2>
        <ul className="mt-4 list-disc space-y-2 pl-5 text-sm text-muted">
          <li>不记录 BOSS 账号和密码，不自动登录或抓取 BOSS。</li>
          <li>API Key 仅通过环境变量读取。</li>
          <li>AI 结果必须经过人工确认后进入正式候选人列表。</li>
          <li>性别、年龄等敏感属性不得参与筛选评分。</li>
        </ul>
      </section>
      <section className="rounded-md border border-line bg-white p-5">
        <h2 className="text-base font-semibold text-ink">腾讯文档模拟同步</h2>
        <p className="mt-2 text-sm text-muted">当前适配器会导出 CSV，并记录最后同步时间；后续可替换为腾讯文档真实 API。</p>
        <button className="mt-4 inline-flex items-center gap-2 rounded-md bg-brand px-4 py-2 text-sm text-white" onClick={exportCsv}>
          <Download size={16} />导出候选人 CSV
        </button>
        {exportResult ? <p className="mt-3 text-sm text-success">{exportResult}</p> : null}
        {error ? <p className="mt-3 text-sm text-danger">{error}</p> : null}
      </section>
    </div>
  );
}
