"use client";

import { useEffect, useMemo, useState } from "react";
import { Bot, BriefcaseBusiness, Building2, ChevronDown, ChevronUp, Clock3, Eye, MapPin, PencilLine, Plus, ShieldCheck, Sparkles, Target, X } from "lucide-react";
import { apiGet, apiPatch, apiPost } from "@/lib/api";
import type { Candidate, JobDescription, ScreeningAssessment } from "@/lib/types";

type Criterion = { id: string; description: string; weight: number };
type RichJob = {
  summary?: string;
  responsibilities?: string[];
  location?: string;
  employment_type?: string;
  must_have?: Criterion[];
  nice_to_have?: Criterion[];
  experience?: { minimum_years?: number; relevant_domains?: string[] };
  screening_policy?: { pass_score?: number; hold_score?: number };
};

type ScreeningProgress = {
  completed: number;
  total: number;
  currentCandidate: string;
};

const exampleJd = {
  title: "后端开发工程师",
  department: "AI 平台部",
  summary: "负责招聘智能化平台核心服务，围绕候选人数据、Agent 工作流和协作系统建设稳定、可审计的后端能力。",
  responsibilities: ["设计候选人、JD 与二筛流程的领域模型和 API", "建设异步任务、事件审计及企业协作系统集成", "通过监控、测试和性能分析保障服务稳定性"],
  location: "上海 / 杭州",
  employment_type: "全职 · 社会招聘",
  must_have: [
    { id: "python", description: "熟练使用 Python，具备良好的工程编码能力", weight: 25 },
    { id: "api", description: "具有 FastAPI 或同类 Web API 开发经验", weight: 25 },
    { id: "database", description: "熟悉 PostgreSQL 或 MySQL 数据建模与性能优化", weight: 20 },
  ],
  nice_to_have: [{ id: "docker", description: "有 Docker、Kubernetes 或云原生实践", weight: 10 }],
  education: { minimum_degree: "本科", preferred_majors: ["计算机科学与技术", "软件工程"] },
  experience: { minimum_years: 2, relevant_domains: ["Web 后端", "分布式系统", "AI 应用工程"] },
  disqualifiers: ["简历中不存在任何后端工程项目或工作证据"],
  screening_policy: { pass_score: 65, hold_score: 45 },
};

export function JobsClient() {
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [assessments, setAssessments] = useState<ScreeningAssessment[]>([]);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [jobCode, setJobCode] = useState("BE-2026-001");
  const [version, setVersion] = useState(1);
  const [jsonText, setJsonText] = useState(JSON.stringify(exampleJd, null, 2));
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [screeningJobId, setScreeningJobId] = useState<number | null>(null);
  const [screeningProgress, setScreeningProgress] = useState<ScreeningProgress | null>(null);
  const [confirmingAssessmentId, setConfirmingAssessmentId] = useState<number | null>(null);
  const [evidenceAssessmentId, setEvidenceAssessmentId] = useState<number | null>(null);

  function load() {
    Promise.all([
      apiGet<JobDescription[]>("/api/job-descriptions"),
      apiGet<Candidate[]>("/api/candidates"),
    ]).then(([nextJobs, nextCandidates]) => {
      setJobs(nextJobs);
      setCandidates(nextCandidates);
      setSelectedJobId((current) => {
        const stored = window.localStorage.getItem("recruitflow_selected_job_id");
        const preferred = current || stored || "";
        return nextJobs.some((job) => String(job.id) === preferred)
          ? preferred
          : (nextJobs[0] ? String(nextJobs[0].id) : "");
      });
    }).catch((reason: Error) => setError(reason.message));
  }
  useEffect(load, []);
  useEffect(() => {
    if (!selectedJobId) return;
    apiGet<ScreeningAssessment[]>(`/api/screening-assessments?job_description_id=${selectedJobId}`)
      .then(setAssessments)
      .catch((reason: Error) => setError(reason.message));
  }, [selectedJobId]);
  const departments = useMemo(() => new Set(jobs.map((job) => job.department)).size, [jobs]);

  function selectJob(value: string) {
    setSelectedJobId(value);
    window.localStorage.setItem("recruitflow_selected_job_id", value);
  }

  async function save() {
    setError(null);
    try {
      const jd = JSON.parse(jsonText) as Record<string, unknown>;
      if (editingId) {
        await apiPatch<JobDescription>(`/api/job-descriptions/${editingId}`, { status: "active", jd });
        setMessage("JD JSON 校验通过，已更新启用版本。");
      } else {
        await apiPost<JobDescription>("/api/job-descriptions", { job_code: jobCode, version, status: "active", jd });
        setMessage("JD JSON 校验通过，已创建启用版本。");
      }
      setEditingId(null); setEditorOpen(false); load();
    } catch (reason) { setError((reason as Error).message); }
  }

  async function screenPending(job: JobDescription) {
    const eligible = candidates.filter((candidate) =>
      candidate.current_status === "active"
      && candidate.current_stage === "待用人部门二筛"
      && candidate.applied_position === job.title
    );
    if (!eligible.length) {
      setError(`当前没有处于“待用人部门二筛”且应聘 ${job.title} 的候选人。`);
      return;
    }
    setError(null); setScreeningJobId(job.id); setMessage(`准备使用 ${job.job_code} 逐条二筛 ${eligible.length} 位候选人。`);
    try {
      for (let index = 0; index < eligible.length; index += 1) {
        const candidate = eligible[index];
        const candidateName = candidate.name || `候选人 #${candidate.id}`;
        setScreeningProgress({ completed: index, total: eligible.length, currentCandidate: candidateName });
        let assessment: ScreeningAssessment;
        try {
          assessment = await apiPost<ScreeningAssessment>(`/api/candidates/${candidate.id}/agent-screen`, { job_description_id: job.id });
        } catch (reason) {
          throw new Error(`筛选 ${candidateName} 失败：${(reason as Error).message}`);
        }
        setAssessments((current) => [assessment, ...current.filter((item) => item.id !== assessment.id)]);
        setScreeningProgress({ completed: index + 1, total: eligible.length, currentCandidate: candidateName });
      }
      setMessage(`批量二筛完成，${eligible.length} 份建议已逐条写入审计表；腾讯文档和企业微信正在后台自动处理。`);
      const nextAssessments = await apiGet<ScreeningAssessment[]>(`/api/screening-assessments?job_description_id=${job.id}`);
      setAssessments(nextAssessments);
    } catch (reason) { setError((reason as Error).message); } finally { setScreeningJobId(null); setScreeningProgress(null); }
  }

  async function confirmAssessment(assessmentId: number, decision: "pass" | "hold" | "reject") {
    setConfirmingAssessmentId(assessmentId);
    setError(null);
    try {
      await apiPost<ScreeningAssessment>(`/api/screening-assessments/${assessmentId}/confirm`, { decision });
      setMessage("人工结论已保存，招聘阶段、审计日志和腾讯文档已同步。");
      const nextAssessments = await apiGet<ScreeningAssessment[]>(`/api/screening-assessments?job_description_id=${selectedJobId}`);
      setAssessments(nextAssessments);
      load();
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setConfirmingAssessmentId(null);
    }
  }

  function edit(job: JobDescription) {
    setEditingId(job.id); setJobCode(job.job_code); setVersion(job.version); setJsonText(JSON.stringify(job.content, null, 2)); setEditorOpen(true);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand">Job architecture</p><h1 className="mt-1 text-2xl font-semibold text-ink">JD 与 AI 二筛</h1><p className="mt-1 max-w-3xl text-sm text-muted">参考真实招聘官网的“岗位职责 + 任职要求”结构，Agent 只基于简历原文给建议，人工确认后才改变阶段。</p></div>
        <button className="flex items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 py-2.5 text-sm font-medium text-white shadow-sm" onClick={() => { setEditingId(null); setJsonText(JSON.stringify(exampleJd, null, 2)); setEditorOpen((value) => !value); }}><Plus size={17} />新建 JD {editorOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}</button>
      </div>

      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        <Metric icon={BriefcaseBusiness} label="JD 版本" value={jobs.length} />
        <Metric icon={Building2} label="覆盖部门" value={departments} />
        <Metric icon={Sparkles} label="启用岗位" value={jobs.filter((job) => job.status === "active").length} />
        <Metric icon={Bot} label="二筛模型" value="DeepSeek" />
      </div>

      {message ? <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-700">{message}</div> : null}
      {error ? <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{error}</div> : null}

      <ScreeningWorkbench
        jobs={jobs}
        candidates={candidates}
        assessments={assessments}
        selectedJobId={selectedJobId}
        screeningJobId={screeningJobId}
        screeningProgress={screeningProgress}
        confirmingAssessmentId={confirmingAssessmentId}
        onSelectJob={selectJob}
        onScreen={() => {
          const job = jobs.find((item) => item.id === Number(selectedJobId));
          if (job) screenPending(job);
        }}
        onConfirm={confirmAssessment}
        onOpenEvidence={setEvidenceAssessmentId}
      />

      {evidenceAssessmentId ? <EvidenceModal assessment={assessments.find((item) => item.id === evidenceAssessmentId) || null} candidate={candidates.find((item) => item.id === assessments.find((assessment) => assessment.id === evidenceAssessmentId)?.candidate_id) || null} onClose={() => setEvidenceAssessmentId(null)} /> : null}

      {editorOpen ? <section className="grid overflow-hidden rounded-xl border border-line bg-white shadow-sm lg:grid-cols-[300px_1fr]">
        <div className="border-b border-line bg-slate-50 p-6 lg:border-b-0 lg:border-r"><p className="text-xs font-semibold uppercase tracking-wide text-brand">Structured JD</p><h2 className="mt-2 text-lg font-semibold text-ink">{editingId ? "编辑岗位版本" : "创建岗位版本"}</h2><p className="mt-2 text-sm leading-6 text-muted">JSON 会在后端执行字段、权重和阈值校验。职责用于业务阅读，筛选标准用于 Agent 评分。</p><div className="mt-5 space-y-3"><label className="block text-xs font-medium text-slate-600">JD 编号<input className="mt-1 w-full rounded-lg border border-line bg-white px-3 py-2 text-sm" value={jobCode} disabled={editingId !== null} onChange={(event) => setJobCode(event.target.value)} /></label><label className="block text-xs font-medium text-slate-600">版本<input type="number" min={1} className="mt-1 w-full rounded-lg border border-line bg-white px-3 py-2 text-sm" value={version} disabled={editingId !== null} onChange={(event) => setVersion(Number(event.target.value))} /></label></div></div>
        <div className="p-5"><textarea aria-label="JD JSON" className="h-[430px] w-full rounded-lg border border-slate-200 bg-slate-950 p-4 font-mono text-xs leading-5 text-slate-100 outline-none focus:border-brand" value={jsonText} onChange={(event) => setJsonText(event.target.value)} /><div className="mt-3 flex justify-end gap-2"><button className="rounded-lg border border-line px-4 py-2 text-sm" onClick={() => setEditorOpen(false)}>取消</button><button className="rounded-lg bg-brand px-4 py-2 text-sm font-medium text-white" onClick={save}>校验并保存</button></div></div>
      </section> : null}

      <section className="grid gap-4 xl:grid-cols-2">
        {jobs.map((job) => <JobCard key={job.id} job={job} onEdit={() => edit(job)} />)}
      </section>
      {!jobs.length ? <div className="rounded-xl border border-dashed border-line bg-white p-8 text-center text-sm text-muted">暂无 JD，请使用用人部门账号创建。</div> : null}
    </div>
  );
}

function JobCard({ job, onEdit }: { job: JobDescription; onEdit: () => void }) {
  const content = job.content as RichJob;
  const criteria = [...(content.must_have || []), ...(content.nice_to_have || [])];
  return <article className="flex flex-col rounded-xl border border-line bg-white p-5 shadow-sm transition-shadow hover:shadow-md"><div className="flex items-start justify-between gap-4"><div><div className="flex flex-wrap items-center gap-2"><span className="rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-brand">{job.job_code} · v{job.version}</span><span className="rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700">{job.status === "active" ? "招聘中" : job.status}</span></div><h2 className="mt-3 text-lg font-semibold text-ink">{job.title}</h2><p className="mt-1 flex items-center gap-1 text-sm text-muted"><Building2 size={14} />{job.department}</p></div><div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-blue-50 to-indigo-100 text-brand"><BriefcaseBusiness size={20} /></div></div><p className="mt-4 line-clamp-2 text-sm leading-6 text-slate-600">{content.summary || "该岗位尚未补充岗位概述。"}</p><div className="mt-4 flex flex-wrap gap-x-4 gap-y-2 text-xs text-muted"><span className="flex items-center gap-1"><MapPin size={14} />{content.location || "地点待定"}</span><span className="flex items-center gap-1"><Clock3 size={14} />{content.employment_type || "全职"}</span><span className="flex items-center gap-1"><Target size={14} />通过线 {content.screening_policy?.pass_score ?? "-"} 分</span></div><div className="mt-4 border-t border-line pt-4"><p className="text-xs font-medium text-slate-500">核心筛选标准</p><div className="mt-2 flex flex-wrap gap-2">{criteria.slice(0, 4).map((item) => <span key={item.id} title={item.description} className="rounded-full border border-line bg-slate-50 px-2.5 py-1 text-xs text-slate-600">{item.description} · {item.weight}</span>)}</div></div><div className="mt-auto pt-5"><button className="flex items-center gap-1.5 rounded-lg border border-line px-3 py-2 text-sm text-slate-700 hover:border-brand hover:text-brand" onClick={onEdit}><PencilLine size={15} />编辑 JD</button></div></article>;
}

function ScreeningWorkbench({ jobs, candidates, assessments, selectedJobId, screeningJobId, screeningProgress, confirmingAssessmentId, onSelectJob, onScreen, onConfirm, onOpenEvidence }: {
  jobs: JobDescription[];
  candidates: Candidate[];
  assessments: ScreeningAssessment[];
  selectedJobId: string;
  screeningJobId: number | null;
  screeningProgress: ScreeningProgress | null;
  confirmingAssessmentId: number | null;
  onSelectJob: (value: string) => void;
  onScreen: () => void;
  onConfirm: (assessmentId: number, decision: "pass" | "hold" | "reject") => void;
  onOpenEvidence: (assessmentId: number) => void;
}) {
  const candidateById = new Map(candidates.map((candidate) => [candidate.id, candidate]));
  const latestByCandidate = new Map<number, ScreeningAssessment>();
  for (const assessment of assessments) {
    if (!latestByCandidate.has(assessment.candidate_id)) latestByCandidate.set(assessment.candidate_id, assessment);
  }
  const latest = Array.from(latestByCandidate.values());
  const selectedJob = jobs.find((job) => job.id === Number(selectedJobId));
  const pending = latest.filter((assessment) => assessment.status !== "confirmed").length;

  return <section className="overflow-hidden rounded-xl border border-blue-200 bg-white shadow-sm">
    <div className="grid gap-4 bg-gradient-to-r from-slate-950 to-blue-950 p-5 text-white lg:grid-cols-[1fr_auto] lg:items-end">
      <div><div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-blue-300"><ShieldCheck size={15} />AI screening workbench</div><h2 className="mt-2 text-xl font-semibold">批量二筛与人工审计</h2><p className="mt-1 text-sm text-slate-300">选择 JD 后逐条筛选该岗位全部待二筛候选人；完成一条，审计表立即出现一条。</p><div className="mt-4 flex flex-col gap-2 sm:flex-row"><select aria-label="批量二筛 JD" className="min-w-0 flex-1 rounded-lg border border-white/20 bg-white px-3 py-2.5 text-sm text-slate-900" value={selectedJobId} onChange={(event) => onSelectJob(event.target.value)}>{jobs.filter((job) => job.status === "active").map((job) => <option key={job.id} value={job.id}>{job.job_code} · {job.title} · {job.department}</option>)}</select><button disabled={!selectedJob || screeningJobId !== null} className="flex items-center justify-center gap-2 rounded-lg bg-blue-500 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-400 disabled:opacity-50" onClick={onScreen}><Bot size={17} />{screeningJobId ? `正在筛选 ${screeningProgress?.completed || 0}/${screeningProgress?.total || 0}` : "立即批量二筛"}</button></div>{screeningProgress ? <div className="mt-3 rounded-lg border border-white/15 bg-white/10 p-3"><div className="flex items-center justify-between gap-3 text-xs"><span className="font-medium text-white">正在筛选：{screeningProgress.currentCandidate}</span><span className="text-blue-200">{screeningProgress.completed} / {screeningProgress.total}</span></div><div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white/15"><div className="h-full rounded-full bg-blue-400 transition-all" style={{ width: `${Math.max(4, screeningProgress.total ? screeningProgress.completed / screeningProgress.total * 100 : 0)}%` }} /></div><p className="mt-2 text-xs text-slate-300">该候选人完成后会立刻加入下方审计表，不需要等待整批结束。</p></div> : null}</div>
      <div className="grid grid-cols-3 gap-2 text-center lg:min-w-[280px]"><WorkbenchMetric label="最新评估" value={latest.length} /><WorkbenchMetric label="待确认" value={pending} /><WorkbenchMetric label="已确认" value={latest.length - pending} /></div>
    </div>
    <div className="border-b border-line px-5 py-4"><div className="flex items-center justify-between"><div><h3 className="font-semibold text-ink">二筛审计表</h3><p className="mt-0.5 text-xs text-muted">只展示每位候选人在当前 JD 下的最新评估；人工结论选择后立即写入审计日志并同步腾讯文档。</p></div><span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">{pending} 条待处理</span></div></div>
    {latest.length ? <div className="overflow-x-auto"><table className="w-full min-w-[920px] text-sm"><thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500"><tr><th className="px-5 py-3">候选人</th><th className="px-4 py-3">Agent 评分</th><th className="px-4 py-3">硬性门槛</th><th className="px-4 py-3">证据摘要</th><th className="px-4 py-3">状态</th><th className="px-5 py-3">人工结论</th></tr></thead><tbody>{latest.map((assessment) => {
      const candidate = candidateById.get(assessment.candidate_id);
      const evidenceCount = assessment.criteria_results.reduce((sum, item) => sum + item.evidence.length, 0);
      const legacy = assessment.prompt_version !== "screening-v2";
      return <tr key={assessment.id} className="border-t border-line align-middle hover:bg-blue-50/30"><td className="px-5 py-4"><p className="font-medium text-ink">{candidate?.name || `候选人 #${assessment.candidate_id}`}</p><p className="mt-0.5 text-xs text-muted">{candidate?.applied_position || "-"} · 评估 #{assessment.id} · {assessment.prompt_version}</p></td><td className="px-4 py-4"><div className="flex items-center gap-2"><span className="text-lg font-semibold text-ink">{assessment.total_score}</span><RecommendationBadge value={assessment.recommendation} legacy={legacy} /></div></td><td className="px-4 py-4">{legacy && assessment.hard_requirement_failures.length ? <span className="rounded-md bg-amber-50 px-2 py-1 text-xs text-amber-700">旧规则推断，需重跑</span> : assessment.hard_requirement_failures.length ? <span className="rounded-md bg-rose-50 px-2 py-1 text-xs text-rose-700">原文明示不满足 {assessment.hard_requirement_failures.length} 项</span> : <span className="rounded-md bg-emerald-50 px-2 py-1 text-xs text-emerald-700">无明确反证</span>}</td><td className="px-4 py-4"><button className="group text-left" onClick={() => onOpenEvidence(assessment.id)}><span className="flex items-center gap-1 text-slate-700 group-hover:text-brand"><Eye size={15} className="text-brand" />查看全部 {evidenceCount} 条证据</span><p className="mt-1 max-w-[260px] truncate text-xs text-muted group-hover:text-brand">{assessment.summary}</p></button></td><td className="px-4 py-4">{assessment.status === "confirmed" ? <span className="text-emerald-700">已确认 · {decisionLabel(assessment.human_decision)}</span> : legacy ? <span className="text-amber-700">待重跑 / 人工确认</span> : <span className="text-amber-700">待人工确认</span>}<p className="mt-1 text-xs text-muted">同步：{syncStatusLabel(assessment.sync_status)}</p></td><td className="px-5 py-4">{assessment.status === "confirmed" ? <div><p className="text-sm font-medium text-ink">{assessment.human_actor || "未记录姓名"}</p><p className="mt-0.5 text-xs text-muted">{roleLabel(assessment.human_role)} · {assessment.human_username || "历史记录无账号"}</p></div> : <select aria-label={`评估 ${assessment.id} 人工结论`} disabled={confirmingAssessmentId !== null} defaultValue="" className="rounded-lg border border-line bg-white px-3 py-2 text-sm" onChange={(event) => { const value = event.target.value as "pass" | "hold" | "reject"; if (value) onConfirm(assessment.id, value); }}><option value="" disabled>{confirmingAssessmentId === assessment.id ? "保存中…" : "选择结论"}</option><option value="pass">确认通过</option><option value="hold">待沟通</option><option value="reject">确认不通过</option></select>}</td></tr>;
    })}</tbody></table></div> : <div className="p-8 text-center text-sm text-muted">当前 JD 尚无二筛结果，点击上方“立即批量二筛”生成审计记录。</div>}
  </section>;
}

function WorkbenchMetric({ label, value }: { label: string; value: number }) { return <div className="rounded-lg bg-white/10 px-3 py-3"><p className="text-xl font-semibold">{value}</p><p className="mt-0.5 text-xs text-slate-300">{label}</p></div>; }
function RecommendationBadge({ value, legacy }: { value: ScreeningAssessment["recommendation"]; legacy: boolean }) { const styles = value === "pass" ? "bg-emerald-50 text-emerald-700" : value === "hold" ? "bg-amber-50 text-amber-700" : "bg-rose-50 text-rose-700"; return <span className={`rounded-md px-2 py-1 text-xs ${styles}`}>{legacy ? "历史建议 · " : ""}{decisionLabel(value)}</span>; }
function decisionLabel(value: string | null) { return value === "pass" ? "通过" : value === "hold" ? "待沟通" : value === "reject" ? "不通过" : "-"; }
function roleLabel(value: string | null) { return value === "department" ? "用人部门审批人" : value === "hr" ? "HR 审批人" : "历史角色未记录"; }
function syncStatusLabel(value: string) { return value === "synced" ? "腾讯文档已同步" : value === "queued" || value === "pending" ? "后台同步中" : value === "unconfigured" ? "腾讯文档未配置" : value === "failed" ? "同步失败，见事件日志" : value; }

function EvidenceModal({ assessment, candidate, onClose }: { assessment: ScreeningAssessment | null; candidate: Candidate | null; onClose: () => void }) {
  if (!assessment) return null;
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/55 px-4 py-6" role="presentation" onMouseDown={onClose}>
    <div className="max-h-full w-full max-w-4xl overflow-hidden rounded-2xl border border-line bg-white shadow-2xl" role="dialog" aria-modal="true" aria-labelledby="evidence-title" onMouseDown={(event) => event.stopPropagation()}>
      <div className="flex items-start justify-between gap-4 border-b border-line bg-slate-50 px-5 py-4"><div><p className="text-xs font-semibold uppercase tracking-[0.16em] text-brand">Assessment #{assessment.id}</p><h2 id="evidence-title" className="mt-1 text-xl font-semibold text-ink">{candidate?.name || `候选人 #${assessment.candidate_id}`} · 完整证据</h2><p className="mt-1 text-sm text-muted">{assessment.model} · {assessment.prompt_version} · {assessment.total_score} 分 · 建议{decisionLabel(assessment.recommendation)}</p>{assessment.status === "confirmed" ? <p className="mt-1 text-xs font-medium text-emerald-700">审批：{assessment.human_actor || "未记录姓名"} · {roleLabel(assessment.human_role)} · {assessment.human_username || "历史记录无账号"}</p> : null}</div><button className="rounded-lg border border-line bg-white p-2 text-slate-500 hover:text-ink" onClick={onClose} aria-label="关闭完整证据"><X size={18} /></button></div>
      <div className="max-h-[calc(100vh-170px)] overflow-y-auto p-5">
        <div className="rounded-xl border border-blue-100 bg-blue-50 p-4"><p className="text-xs font-medium text-blue-700">Agent 总结</p><p className="mt-2 text-sm leading-6 text-slate-700">{assessment.summary}</p></div>
        {assessment.hard_requirement_failures.length ? <section className="mt-5"><h3 className="font-semibold text-rose-700">硬性要求明确反证</h3><div className="mt-2 space-y-2">{assessment.hard_requirement_failures.map((failure, index) => <blockquote key={`${failure}-${index}`} className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">“{failure}”</blockquote>)}</div></section> : null}
        <section className="mt-5"><h3 className="font-semibold text-ink">逐项评分与简历原文</h3><div className="mt-3 space-y-3">{assessment.criteria_results.map((criterion) => <article key={criterion.criterion_id} className="rounded-xl border border-line p-4"><div className="flex flex-wrap items-center justify-between gap-2"><div className="flex items-center gap-2"><span className="font-mono text-sm font-semibold text-ink">{criterion.criterion_id}</span><span className={`rounded-full px-2 py-0.5 text-xs ${criterion.matched ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>{criterion.matched ? "匹配" : "未匹配"}</span></div><span className="text-sm font-semibold text-ink">{criterion.score} 分</span></div><p className="mt-2 text-sm leading-6 text-slate-600">{criterion.reasoning}</p>{criterion.evidence.length ? <div className="mt-3 space-y-2">{criterion.evidence.map((quote, index) => <blockquote key={`${quote}-${index}`} className="rounded-lg border-l-4 border-brand bg-slate-50 px-3 py-2 text-sm leading-6 text-slate-700">“{quote}”</blockquote>)}</div> : <p className="mt-3 text-xs text-muted">简历中没有可引用的匹配证据。</p>}</article>)}</div></section>
        {assessment.risk_points.length ? <section className="mt-5"><h3 className="font-semibold text-ink">风险与信息缺口</h3><ul className="mt-2 space-y-2 text-sm text-slate-700">{assessment.risk_points.map((risk, index) => <li key={`${risk}-${index}`} className="rounded-lg bg-amber-50 px-3 py-2">{risk}</li>)}</ul></section> : null}
        {assessment.interview_questions.length ? <section className="mt-5"><h3 className="font-semibold text-ink">建议追问</h3><ol className="mt-2 space-y-2 text-sm text-slate-700">{assessment.interview_questions.map((question, index) => <li key={`${question}-${index}`} className="rounded-lg bg-slate-50 px-3 py-2">{index + 1}. {question}</li>)}</ol></section> : null}
      </div>
    </div>
  </div>;
}

function Metric({ icon: Icon, label, value }: { icon: typeof BriefcaseBusiness; label: string; value: number | string }) {
  return <div className="rounded-xl border border-line bg-white p-4 shadow-sm"><div className="flex items-center gap-2 text-xs text-muted"><Icon size={15} className="text-brand" />{label}</div><p className="mt-2 text-2xl font-semibold text-ink">{value}</p></div>;
}
