"use client";

import { useEffect, useState } from "react";
import { Bot, Send, ShieldCheck } from "lucide-react";
import { apiGet, apiPost, maskEmail, maskPhone } from "@/lib/api";
import { StageBadge } from "@/lib/stages";
import type { Candidate, EventLog, JobDescription, ScreeningAssessment } from "@/lib/types";
import { ErrorBlock, LoadingBlock } from "./StateBlock";

const recommendationText = { pass: "建议通过", hold: "建议待沟通", reject: "建议不通过" };

export function CandidateScreeningClient({ id }: { id: string }) {
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [events, setEvents] = useState<EventLog[]>([]);
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [assessments, setAssessments] = useState<ScreeningAssessment[]>([]);
  const [jobId, setJobId] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  function load() {
    Promise.all([
      apiGet<Candidate>(`/api/candidates/${id}`),
      apiGet<EventLog[]>(`/api/candidates/${id}/events`)
    ]).then(([nextCandidate, nextEvents]) => {
      setCandidate(nextCandidate);
      setEvents(nextEvents);
    }).catch((reason: Error) => setError(reason.message));
    Promise.all([
      apiGet<JobDescription[]>("/api/job-descriptions?status=active"),
      apiGet<ScreeningAssessment[]>(`/api/candidates/${id}/assessments`)
    ]).then(([nextJobs, nextAssessments]) => {
      setJobs(nextJobs);
      setAssessments(nextAssessments);
      setJobId((current) => current || (nextJobs.length ? String(nextJobs[0].id) : ""));
    }).catch((reason: Error) => setError(`请先在“角色登录”中登录：${reason.message}`));
  }

  useEffect(load, [id]);

  async function runAgent() {
    if (!jobId) return;
    setBusy(true);
    setError(null);
    setMessage("DeepSeek V4 Flash 正在逐项引用简历证据并评分…");
    try {
      await apiPost<ScreeningAssessment>(`/api/candidates/${id}/agent-screen`, { job_description_id: Number(jobId) });
      setMessage("Agent 建议已生成，等待用人部门确认；招聘阶段尚未改变。");
      load();
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function confirm(assessment: ScreeningAssessment, decision: "pass" | "hold" | "reject") {
    setBusy(true);
    setError(null);
    try {
      await apiPost<ScreeningAssessment>(`/api/screening-assessments/${assessment.id}/confirm`, { decision });
      setMessage("人工结论已保存，招聘阶段、审计日志和腾讯文档已同步。");
      load();
    } catch (reason) {
      setError((reason as Error).message);
      load();
    } finally {
      setBusy(false);
    }
  }

  async function sendCard(assessment: ScreeningAssessment) {
    try {
      const result = await apiPost<{ channel: string; status: string }>(`/api/candidates/${id}/send-screening-card?assessment_id=${assessment.id}`);
      setMessage(`企业微信二筛通知已发送：${result.channel} / ${result.status}`);
    } catch (reason) {
      setError((reason as Error).message);
    }
  }

  if (!candidate && error) return <ErrorBlock message={error} />;
  if (!candidate) return <LoadingBlock />;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold text-ink">{candidate.name || "候选人详情"}</h1>
        <div className="mt-2 flex items-center gap-2 text-sm text-muted">
          <span>{candidate.applied_position || "-"}</span><StageBadge stage={candidate.current_stage} />
        </div>
      </div>
      {message ? <div className="rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-brand">{message}</div> : null}
      {error ? <div className="rounded-md border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div> : null}

      <section className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-md border border-line bg-white p-5 lg:col-span-2">
          <h2 className="mb-4 font-semibold text-ink">候选人信息</h2>
          <dl className="grid gap-3 text-sm md:grid-cols-2">
            <div><dt className="text-muted">联系方式</dt><dd>{maskPhone(candidate.phone)} / {maskEmail(candidate.email)}</dd></div>
            <div><dt className="text-muted">学校专业</dt><dd>{candidate.school || "-"} / {candidate.major || "-"}</dd></div>
            <div><dt className="text-muted">学历毕业</dt><dd>{candidate.degree || "-"} / {candidate.graduation_date || "-"}</dd></div>
            <div><dt className="text-muted">负责人</dt><dd>{candidate.hr_owner || "-"} / {candidate.department || "-"}</dd></div>
          </dl>
          <p className="mt-4 text-sm leading-6 text-ink">{candidate.ai_summary || "暂无摘要"}</p>
        </div>
        <div className="rounded-md border border-line bg-white p-5">
          <h2 className="mb-3 flex items-center gap-2 font-semibold text-ink"><Bot size={18} />执行 AI 二筛</h2>
          <select aria-label="选择 JD" className="w-full rounded-md border border-line px-3 py-2 text-sm" value={jobId} onChange={(event) => setJobId(event.target.value)}>
            <option value="">选择启用的 JD</option>
            {jobs.map((job) => <option key={job.id} value={job.id}>{job.job_code} · {job.title} v{job.version}</option>)}
          </select>
          <button disabled={!jobId || busy} className="mt-3 flex w-full items-center justify-center gap-2 rounded-md bg-brand px-3 py-2 text-sm text-white disabled:opacity-40" onClick={runAgent}>
            <Bot size={16} />{busy ? "处理中…" : "运行 DeepSeek 二筛"}
          </button>
          <p className="mt-3 text-xs leading-5 text-muted">Agent 只给建议，不会自动改变招聘阶段。所有匹配点必须引用简历原文。</p>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-lg font-semibold text-ink">二筛评估记录</h2>
        {assessments.map((assessment) => (
          <article key={assessment.id} className="rounded-md border border-line bg-white p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="text-sm font-medium text-brand">评估 #{assessment.id} · {assessment.model}</p>
                <h3 className="mt-1 text-lg font-semibold text-ink">{assessment.total_score} 分 · {recommendationText[assessment.recommendation]}</h3>
              </div>
              <span className="rounded bg-slate-100 px-2 py-1 text-xs text-slate-600">{assessment.status === "confirmed" ? `人工结论：${assessment.human_decision}` : "待人工确认"}</span>
            </div>
            <p className="mt-3 text-sm leading-6 text-ink">{assessment.summary}</p>
            <div className="mt-4 space-y-3">
              {assessment.criteria_results.map((criterion) => (
                <div key={criterion.criterion_id} className="rounded-md border border-line p-3 text-sm">
                  <p className="font-medium text-ink">{criterion.criterion_id} · {criterion.score} 分 · {criterion.matched ? "匹配" : "未匹配"}</p>
                  <p className="mt-1 text-muted">{criterion.reasoning}</p>
                  {criterion.evidence.map((evidence) => <blockquote key={evidence} className="mt-2 border-l-2 border-blue-300 pl-3 text-slate-600">“{evidence}”</blockquote>)}
                </div>
              ))}
            </div>
            <div className="mt-4 flex flex-wrap gap-2">
              <button className="flex items-center gap-2 rounded-md border border-blue-200 px-3 py-2 text-sm text-brand" onClick={() => sendCard(assessment)}><Send size={15} />发送企业微信</button>
              {assessment.status !== "confirmed" ? <>
                <button disabled={busy} className="flex items-center gap-2 rounded-md bg-emerald-600 px-3 py-2 text-sm text-white" onClick={() => confirm(assessment, "pass")}><ShieldCheck size={15} />确认通过</button>
                <button disabled={busy} className="rounded-md border border-amber-300 px-3 py-2 text-sm text-amber-700" onClick={() => confirm(assessment, "hold")}>待沟通</button>
                <button disabled={busy} className="rounded-md border border-rose-300 px-3 py-2 text-sm text-rose-700" onClick={() => confirm(assessment, "reject")}>确认不通过</button>
              </> : null}
            </div>
            <p className="mt-3 text-xs text-muted">Prompt {assessment.prompt_version} · 输入 {assessment.input_tokens} tokens · 输出 {assessment.output_tokens} tokens · 成本 ${assessment.api_cost.toFixed(6)}</p>
          </article>
        ))}
        {!assessments.length ? <div className="rounded-md border border-dashed border-line p-5 text-sm text-muted">尚未执行基于 JD 的 Agent 二筛。</div> : null}
      </section>

      <section className="rounded-md border border-line bg-white p-5">
        <h2 className="mb-3 font-semibold text-ink">事件审计记录</h2>
        <div className="space-y-2 text-sm">{events.map((event) => <div key={event.id} className="rounded border border-line p-3"><span className="font-medium">{event.event_type}</span><span className="ml-2 text-muted">{event.actor} · {new Date(event.created_at).toLocaleString()}</span>{event.note ? <p className="mt-1 text-muted">{event.note}</p> : null}</div>)}</div>
      </section>
    </div>
  );
}
