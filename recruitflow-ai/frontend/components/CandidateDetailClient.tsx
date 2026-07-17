"use client";

import { useEffect, useState } from "react";
import { Send, ThumbsDown, ThumbsUp } from "lucide-react";
import { apiGet, apiPatch, apiPost, maskEmail, maskPhone } from "@/lib/api";
import type { Candidate, EventLog } from "@/lib/types";
import { ErrorBlock, LoadingBlock } from "./StateBlock";

export function CandidateDetailClient({ id }: { id: string }) {
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [events, setEvents] = useState<EventLog[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    Promise.all([apiGet<Candidate>(`/api/candidates/${id}`), apiGet<EventLog[]>(`/api/candidates/${id}/events`)])
      .then(([nextCandidate, nextEvents]) => {
        setCandidate(nextCandidate);
        setEvents(nextEvents);
      })
      .catch((reason: Error) => setError(reason.message));
  }

  useEffect(load, [id]);

  async function screening(result: "pass" | "reject" | "hold") {
    const updated = await apiPost<Candidate>(`/api/candidates/${id}/screening-result`, { result, actor: "HR Demo" });
    setCandidate(updated);
    setMessage("二筛结果已记录，阶段已按规则更新。");
    load();
  }

  async function setStage(stage: string) {
    const updated = await apiPatch<Candidate>(`/api/candidates/${id}/stage`, { stage, actor: "HR Demo" });
    setCandidate(updated);
    setMessage("阶段已更新。");
    load();
  }

  async function sendCard() {
    const result = await apiPost<{ status: string; channel: string }>(`/api/candidates/${id}/send-screening-card`);
    setMessage(`二筛卡片已发送：${result.channel} / ${result.status}`);
    load();
  }

  if (error) return <ErrorBlock message={error} />;
  if (!candidate) return <LoadingBlock />;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold text-ink">{candidate.name || "候选人详情"}</h1>
        <p className="mt-1 text-sm text-muted">{candidate.applied_position || "-"} · {candidate.current_stage}</p>
      </div>
      {message ? <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-brand">{message}</div> : null}
      <section className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-md border border-line bg-white p-5 lg:col-span-2">
          <h2 className="mb-4 text-base font-semibold text-ink">基础信息</h2>
          <dl className="grid gap-3 text-sm md:grid-cols-2">
            <div><dt className="text-muted">联系方式</dt><dd>{maskPhone(candidate.phone)} / {maskEmail(candidate.email)}</dd></div>
            <div><dt className="text-muted">学校专业</dt><dd>{candidate.school || "-"} / {candidate.major || "-"}</dd></div>
            <div><dt className="text-muted">学历毕业</dt><dd>{candidate.degree || "-"} / {candidate.graduation_date || "-"}</dd></div>
            <div><dt className="text-muted">负责人</dt><dd>{candidate.hr_owner || "-"} / {candidate.department || "-"}</dd></div>
          </dl>
        </div>
        <div className="rounded-md border border-line bg-white p-5">
          <h2 className="mb-4 text-base font-semibold text-ink">操作</h2>
          <div className="space-y-2">
            <button className="flex w-full items-center justify-center gap-2 rounded-md bg-brand px-3 py-2 text-sm text-white" onClick={sendCard}><Send size={16} />发送二筛卡片</button>
            <button className="flex w-full items-center justify-center gap-2 rounded-md border border-line px-3 py-2 text-sm" onClick={() => screening("pass")}><ThumbsUp size={16} />二筛通过</button>
            <button className="flex w-full items-center justify-center gap-2 rounded-md border border-line px-3 py-2 text-sm" onClick={() => screening("reject")}><ThumbsDown size={16} />二筛不通过</button>
            <button className="w-full rounded-md border border-line px-3 py-2 text-sm" onClick={() => setStage("已约面试")}>标记已约面试</button>
            <button className="w-full rounded-md border border-line px-3 py-2 text-sm" onClick={() => setStage("待面试反馈")}>标记待反馈</button>
          </div>
        </div>
      </section>
      <section className="rounded-md border border-line bg-white p-5">
        <p className="mb-2 text-xs font-medium text-brand">AI 生成内容</p>
        <p className="text-sm leading-6 text-ink">{candidate.ai_summary || "暂无 AI 摘要"}</p>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          <List title="匹配点" items={candidate.matching_points} />
          <List title="风险点" items={candidate.risk_points} />
          <List title="面试问题" items={candidate.interview_questions} />
        </div>
      </section>
      <section className="rounded-md border border-line bg-white p-5">
        <h2 className="mb-4 text-base font-semibold text-ink">事件记录</h2>
        <div className="space-y-3">
          {events.map((event) => (
            <div key={event.id} className="rounded-md border border-line p-3 text-sm">
              <p className="font-medium text-ink">{event.event_type}</p>
              <p className="mt-1 text-muted">{event.old_stage || "-"} → {event.new_stage || "-"} · {event.actor} · {new Date(event.created_at).toLocaleString()}</p>
              {event.note ? <p className="mt-1 text-muted">{event.note}</p> : null}
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}

function List({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <h3 className="mb-2 text-sm font-medium text-ink">{title}</h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-muted">
        {items.length ? items.map((item) => <li key={item}>{item}</li>) : <li>暂无</li>}
      </ul>
    </div>
  );
}
