"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { Bot, CheckCircle2, FileText, History, RefreshCw, UserCheck } from "lucide-react";
import { apiGet } from "@/lib/api";
import { StageBadge } from "@/lib/stages";
import type { EventLog } from "@/lib/types";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "./StateBlock";

const eventPresentation: Record<string, { label: string; description: string; tone: string; icon: typeof History }> = {
  demo_candidate_seeded: { label: "Demo 候选人入库", description: "系统写入一条虚构候选人数据", tone: "bg-slate-100 text-slate-700", icon: FileText },
  resume_confirmed: { label: "简历确认入库", description: "HR 已核对 AI 解析结果", tone: "bg-blue-50 text-blue-700", icon: CheckCircle2 },
  candidate_stage_updated: { label: "招聘阶段更新", description: "候选人流程状态发生变化", tone: "bg-violet-50 text-violet-700", icon: RefreshCw },
  agent_screening_completed: { label: "AI 二筛完成", description: "Agent 已生成待人工确认建议", tone: "bg-amber-50 text-amber-700", icon: Bot },
  screening_decision_confirmed: { label: "二筛人工确认", description: "用人部门已确认 Agent 建议", tone: "bg-emerald-50 text-emerald-700", icon: UserCheck },
  screening_result: { label: "二筛结论生效", description: "人工结论已写入招聘流程", tone: "bg-emerald-50 text-emerald-700", icon: UserCheck },
  notification_sent: { label: "协作通知已发送", description: "系统已向配置的协作渠道发送通知", tone: "bg-blue-50 text-blue-700", icon: RefreshCw },
  human_confirmed: { label: "简历人工确认", description: "HR 已确认简历字段并创建候选人", tone: "bg-emerald-50 text-emerald-700", icon: UserCheck },
  ai_parse_success: { label: "AI 简历解析完成", description: "简历结构化结果已进入待确认区", tone: "bg-amber-50 text-amber-700", icon: Bot },
  resume_discovered: { label: "发现新简历", description: "系统监测到一份待处理 PDF", tone: "bg-blue-50 text-blue-700", icon: FileText },
  resume_duplicate_file: { label: "重复简历已识别", description: "文件指纹重复，系统未重复创建候选人", tone: "bg-slate-100 text-slate-700", icon: FileText },
};

function noteItems(note: string | null): string[] {
  if (!note) return [];
  return note.split(";").map((item) => item.trim()).filter(Boolean).map((item) => {
    const [key, ...value] = item.split("=");
    const labels: Record<string, string> = { assessment_id: "评估", jd: "JD", score: "得分", recommendation: "建议", model: "模型", approver_name: "审批人", approver_role: "审批角色", approver_username: "审批账号" };
    return value.length ? `${labels[key] || key}：${value.join("=")}` : item;
  });
}

export function EventsClient() {
  const [events, setEvents] = useState<EventLog[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState("all");
  const [limit, setLimit] = useState(20);

  useEffect(() => {
    apiGet<EventLog[]>("/api/events").then(setEvents).catch((reason: Error) => setError(reason.message));
  }, []);

  const visibleEvents = useMemo(() => {
    if (!events || filter === "all") return events || [];
    return events.filter((event) => filter === "ai" ? event.event_type.includes("agent") : event.event_type.includes("stage") || event.event_type.includes("decision"));
  }, [events, filter]);

  if (error) return <ErrorBlock message={error} />;
  if (!events) return <LoadingBlock />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand">Audit trail</p>
          <h1 className="mt-1 text-2xl font-semibold text-ink">招聘事件日志</h1>
          <p className="mt-1 text-sm text-muted">用业务语言呈现谁在什么时间做了什么，敏感信息不进入日志。</p>
        </div>
        <div className="flex rounded-lg border border-line bg-white p-1">
          {[{ id: "all", label: "全部" }, { id: "ai", label: "AI 事件" }, { id: "workflow", label: "流程变更" }].map((item) => (
            <button key={item.id} onClick={() => { setFilter(item.id); setLimit(20); }} className={`rounded-md px-3 py-1.5 text-sm ${filter === item.id ? "bg-slate-900 text-white" : "text-slate-600 hover:bg-slate-50"}`}>{item.label}</button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Metric label="全部事件" value={events.length} />
        <Metric label="AI 二筛" value={events.filter((event) => event.event_type.includes("agent")).length} />
        <Metric label="人工确认" value={events.filter((event) => event.event_type.includes("decision")).length} />
        <Metric label="候选人覆盖" value={new Set(events.map((event) => event.candidate_id).filter(Boolean)).size} />
      </div>

      {visibleEvents.length === 0 ? <EmptyBlock message="当前筛选下暂无事件。" /> : (
        <div className="overflow-hidden rounded-xl border border-line bg-white shadow-sm">
          {visibleEvents.slice(0, limit).map((event, index) => {
            const presentation = eventPresentation[event.event_type] || { label: event.event_type.replaceAll("_", " "), description: "系统业务事件", tone: "bg-slate-100 text-slate-700", icon: History };
            const Icon = presentation.icon;
            return (
              <article key={event.id} className={`grid gap-4 p-5 md:grid-cols-[44px_1fr_auto] ${index ? "border-t border-line" : ""}`}>
                <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${presentation.tone}`}><Icon size={19} /></div>
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="font-medium text-ink">{presentation.label}</h2>
                    {event.candidate_id ? <Link className="rounded-full bg-blue-50 px-2 py-0.5 text-xs text-brand hover:bg-blue-100" href={`/candidates/${event.candidate_id}`}>候选人 #{event.candidate_id}</Link> : null}
                    <span className="text-xs text-muted">操作者：{event.actor}</span>
                  </div>
                  <p className="mt-1 text-sm text-muted">{presentation.description}</p>
                  {(event.old_stage || event.new_stage) ? <div className="mt-3 flex flex-wrap items-center gap-2"><StageBadge stage={event.old_stage} /><span className="text-slate-400">→</span><StageBadge stage={event.new_stage} /></div> : null}
                  {noteItems(event.note).length ? <div className="mt-3 flex flex-wrap gap-2">{noteItems(event.note).map((item) => <span key={item} className="rounded-md border border-line bg-slate-50 px-2 py-1 text-xs text-slate-600">{item}</span>)}</div> : null}
                </div>
                <time className="whitespace-nowrap text-xs text-muted">{new Date(event.created_at).toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" })}</time>
              </article>
            );
          })}
        </div>
      )}
      {visibleEvents.length > limit ? <div className="text-center"><button className="rounded-lg border border-line bg-white px-4 py-2 text-sm text-slate-600 shadow-sm hover:border-brand hover:text-brand" onClick={() => setLimit((value) => value + 20)}>加载更多（剩余 {visibleEvents.length - limit} 条）</button></div> : null}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return <div className="rounded-xl border border-line bg-white p-4 shadow-sm"><p className="text-xs text-muted">{label}</p><p className="mt-1 text-2xl font-semibold text-ink">{value}</p></div>;
}
