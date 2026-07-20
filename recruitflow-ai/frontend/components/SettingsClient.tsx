"use client";

import { useEffect, useState } from "react";
import { Bot, CheckCircle2, CloudUpload, Download, ExternalLink, KeyRound, MessageSquareText, RefreshCw, Save, ShieldCheck } from "lucide-react";
import { apiGet, apiPatch, apiPost, getSession } from "@/lib/api";

type AiModelSettings = {
  model: string;
  provider: string;
  base_url: string;
  api_key_configured: boolean;
};

type IntegrationSettings = {
  tencent_docs_configured: boolean;
  tencent_docs_file_id: string | null;
  tencent_docs_url: string | null;
  tencent_docs_sync_mode: "automatic_on_change";
  last_tencent_docs_sync_at: string | null;
  wecom_configured: boolean;
  wecom_mode: "automatic_after_screening";
  public_app_url: string;
};

type TencentSyncResult = {
  file_id: string;
  url: string;
  rows: number;
  synced_at: string;
};

export function SettingsClient() {
  const [aiSettings, setAiSettings] = useState<AiModelSettings | null>(null);
  const [model, setModel] = useState("");
  const [savingModel, setSavingModel] = useState(false);
  const [integration, setIntegration] = useState<IntegrationSettings | null>(null);
  const [syncResult, setSyncResult] = useState<TencentSyncResult | null>(null);
  const [exportResult, setExportResult] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const session = getSession();
    apiGet<IntegrationSettings>("/api/settings/integrations")
      .then(setIntegration)
      .catch((reason: Error) => setError(reason.message));
    if (session?.role === "hr") {
      apiGet<AiModelSettings>("/api/settings/ai-model").then((result) => {
        setAiSettings(result);
        setModel(result.model);
      }).catch((reason: Error) => setError(reason.message));
    }
  }, []);

  async function saveModel() {
    setSavingModel(true); setError(null);
    try {
      const result = await apiPatch<AiModelSettings>("/api/settings/ai-model", { model: model.trim() });
      setAiSettings(result); setModel(result.model);
      setExportResult(`AI 模型已切换为 ${result.model}，后续简历解析和二筛立即生效。`);
    } catch (reason) { setError((reason as Error).message); } finally { setSavingModel(false); }
  }

  async function exportCsv() {
    setError(null);
    try {
      const result = await apiPost<{ path: string; rows: number; synced_at: string }>("/api/export/csv");
      setExportResult(`已导出 ${result.rows} 条候选人数据：${result.path}`);
    } catch (reason) { setError((reason as Error).message); }
  }

  async function syncTencentDocs() {
    setError(null); setSyncing(true);
    try {
      const result = await apiPost<TencentSyncResult>("/api/export/tencent-docs");
      setSyncResult(result);
      setIntegration(await apiGet<IntegrationSettings>("/api/settings/integrations"));
      setExportResult(`补偿同步完成，本次写入 ${result.rows} 条候选人变更。`);
    } catch (reason) { setError((reason as Error).message); } finally { setSyncing(false); }
  }

  const tencentDocsUrl = syncResult?.url || integration?.tencent_docs_url;
  const session = getSession();

  return <div className="space-y-6">
    <div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand">Configuration</p><h1 className="mt-1 text-2xl font-semibold text-ink">系统设置</h1><p className="mt-1 text-sm text-muted">管理 AI 模型、数据同步和隐私边界。API Key 始终由服务端环境变量管理。</p></div>
    {exportResult ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{exportResult}</div> : null}
    {error ? <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div> : null}

    {session?.role === "hr" ? <section className="overflow-hidden rounded-xl border border-line bg-white shadow-sm">
      <div className="flex items-center justify-between border-b border-line bg-slate-50 px-5 py-4"><div><h2 className="flex items-center gap-2 font-semibold text-ink"><Bot size={18} className="text-brand" />AI 模型配置</h2><p className="mt-1 text-sm text-muted">填写 OpenRouter 支持的模型 ID，保存后无需重启服务。</p></div>{aiSettings ? <span className={`rounded-full px-3 py-1 text-xs font-medium ${aiSettings.api_key_configured ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"}`}>{aiSettings.api_key_configured ? "API Key 已配置" : "API Key 未配置"}</span> : null}</div>
      <div className="grid gap-5 p-5 lg:grid-cols-[1fr_280px]">
        <div><label className="block text-sm font-medium text-ink">OpenRouter 模型 ID<input className="mt-2 w-full rounded-lg border border-line px-3 py-2.5 font-mono text-sm outline-none focus:border-brand" value={model} onChange={(event) => setModel(event.target.value)} placeholder="例如 deepseek/deepseek-v4-flash" /></label><p className="mt-2 text-xs text-muted">当前项目已验证：deepseek/deepseek-v4-flash。也可以输入其他 OpenRouter 模型 ID。</p><button disabled={!model.trim() || savingModel} className="mt-4 inline-flex items-center gap-2 rounded-lg bg-brand px-4 py-2.5 text-sm font-medium text-white disabled:opacity-50" onClick={saveModel}><Save size={16} />{savingModel ? "保存中…" : "保存并应用"}</button></div>
        <dl className="space-y-3 rounded-lg border border-line bg-slate-50 p-4 text-sm"><div><dt className="text-xs text-muted">Provider</dt><dd className="mt-1 font-medium text-ink">{aiSettings?.provider || "加载中…"}</dd></div><div><dt className="text-xs text-muted">API Base URL</dt><dd className="mt-1 break-all font-mono text-xs text-ink">{aiSettings?.base_url || "-"}</dd></div><div className="flex items-center gap-2 text-xs text-muted"><KeyRound size={14} />Key 不会返回到浏览器</div></dl>
      </div>
    </section> : <section className="rounded-xl border border-line bg-white p-5 shadow-sm"><h2 className="flex items-center gap-2 font-semibold text-ink"><Bot size={18} className="text-brand" />AI 模型配置</h2><p className="mt-2 text-sm text-muted">当前模型由 HR 统一配置。用人部门可以执行二筛和查看每次评估实际使用的模型。</p></section>}

    <section className="rounded-xl border border-line bg-white p-5 shadow-sm"><h2 className="flex items-center gap-2 font-semibold text-ink"><ShieldCheck size={18} />安全与隐私</h2><ul className="mt-4 grid gap-3 text-sm text-muted md:grid-cols-2"><li className="flex gap-2"><CheckCircle2 size={16} className="mt-0.5 text-emerald-500" />不记录 BOSS 账号和密码，不自动登录或抓取。</li><li className="flex gap-2"><CheckCircle2 size={16} className="mt-0.5 text-emerald-500" />API Key 只通过环境变量读取。</li><li className="flex gap-2"><CheckCircle2 size={16} className="mt-0.5 text-emerald-500" />AI 建议由用人部门人工确认后才改变阶段。</li><li className="flex gap-2"><CheckCircle2 size={16} className="mt-0.5 text-emerald-500" />年龄、性别等敏感属性不得参与筛选。</li></ul></section>

    <section className="overflow-hidden rounded-xl border border-line bg-white shadow-sm">
      <div className="border-b border-line bg-slate-50 px-5 py-4"><h2 className="font-semibold text-ink">协作集成</h2><p className="mt-1 text-sm text-muted">HR 与用人部门共享同一份实时台账和群通知状态。</p></div>
      <div className="grid gap-4 p-5 lg:grid-cols-2">
        <div className="rounded-xl border border-line p-4">
          <div className="flex items-start justify-between gap-3"><div><h3 className="flex items-center gap-2 font-medium text-ink"><CloudUpload size={17} className="text-brand" />腾讯文档自动同步</h3><p className="mt-1 text-xs text-muted">候选人确认、字段或阶段变更、AI 二筛和人工结论都会自动同步。</p></div><StatusBadge configured={integration?.tencent_docs_configured ?? false} /></div>
          <dl className="mt-4 grid grid-cols-2 gap-3 rounded-lg bg-slate-50 p-3 text-xs"><div><dt className="text-muted">同步模式</dt><dd className="mt-1 font-medium text-ink">业务变更后自动</dd></div><div><dt className="text-muted">最近全量同步</dt><dd className="mt-1 font-medium text-ink">{integration?.last_tencent_docs_sync_at ? new Date(integration.last_tencent_docs_sync_at).toLocaleString("zh-CN") : "尚未执行"}</dd></div></dl>
          <div className="mt-4 flex flex-wrap gap-2">{tencentDocsUrl ? <a href={tencentDocsUrl} target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-lg bg-brand px-3 py-2 text-sm text-white"><ExternalLink size={15} />打开腾讯文档</a> : null}<button className="inline-flex items-center gap-2 rounded-lg border border-line px-3 py-2 text-sm text-ink" onClick={syncTencentDocs} disabled={syncing || !integration?.tencent_docs_configured}><RefreshCw size={15} className={syncing ? "animate-spin" : ""} />{syncing ? "同步中…" : "立即补偿同步"}</button></div>
          {!integration?.tencent_docs_configured ? <p className="mt-3 text-xs text-amber-700">需要在服务端配置 TENCENT_DOCS_TOKEN；配置后首次同步会自动创建表格并显示链接。</p> : !tencentDocsUrl ? <p className="mt-3 text-xs text-blue-700">Token 已配置，完成一次候选人变更或点击补偿同步后会创建表格并生成链接。</p> : null}
        </div>
        <div className="rounded-xl border border-line p-4">
          <div className="flex items-start justify-between gap-3"><div><h3 className="flex items-center gap-2 font-medium text-ink"><MessageSquareText size={17} className="text-brand" />企业微信群通知</h3><p className="mt-1 text-xs text-muted">每条 AI 二筛完成后自动发送评分、证据摘要和人工确认入口。</p></div><StatusBadge configured={integration?.wecom_configured ?? false} /></div>
          <dl className="mt-4 grid grid-cols-2 gap-3 rounded-lg bg-slate-50 p-3 text-xs"><div><dt className="text-muted">触发时机</dt><dd className="mt-1 font-medium text-ink">每条二筛完成后</dd></div><div><dt className="text-muted">确认入口</dt><dd className="mt-1 break-all font-medium text-ink">{integration?.public_app_url || "-"}</dd></div></dl>
          {integration?.wecom_configured ? <p className="mt-4 text-sm text-emerald-700">真实群机器人 Webhook 已配置，后续二筛会自动推送。</p> : <p className="mt-4 text-sm text-amber-700">尚未配置真实群机器人 Webhook。请在企业微信群添加机器人，将以 https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key= 开头的发送地址写入服务端 WECOM_WEBHOOK_URL 后重启后端。</p>}
        </div>
      </div>
      {session?.role === "hr" ? <div className="border-t border-line px-5 py-4"><button className="inline-flex items-center gap-2 rounded-lg border border-line px-4 py-2.5 text-sm text-ink" onClick={exportCsv}><Download size={16} />导出候选人 CSV</button></div> : null}
    </section>
  </div>;
}

function StatusBadge({ configured }: { configured: boolean }) {
  return <span className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${configured ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`}>{configured ? "已配置" : "未配置"}</span>;
}
