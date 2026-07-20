"use client";

import { useEffect, useState } from "react";
import { CheckCircle, RefreshCw } from "lucide-react";
import { apiGet, apiPost } from "@/lib/api";
import type { Candidate, ResumeFile } from "@/lib/types";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "./StateBlock";

function asText(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function asList(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

export function PendingResumesClient() {
  const [items, setItems] = useState<ResumeFile[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<number | null>(null);

  function load() {
    apiGet<ResumeFile[]>("/api/resumes/pending")
      .then(setItems)
      .catch((reason: Error) => setError(reason.message));
  }

  useEffect(load, []);

  async function confirm(resume: ResumeFile) {
    setBusyId(resume.id);
    setError(null);
    try {
      await apiPost<Candidate>(`/api/resumes/${resume.id}/confirm`, null);
      load();
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusyId(null);
    }
  }

  async function resolveDuplicate(resume: ResumeFile, resolution: "create" | "link") {
    setBusyId(resume.id);
    setError(null);
    try {
      const action = resolution === "create" ? "confirm-new" : "link-duplicate";
      await apiPost<Candidate>(`/api/resumes/${resume.id}/${action}`);
      load();
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusyId(null);
    }
  }

  async function reparse(resume: ResumeFile) {
    setBusyId(resume.id);
    setError(null);
    try {
      await apiPost<ResumeFile>(`/api/resumes/${resume.id}/parse`);
      load();
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusyId(null);
    }
  }

  if (error) return <ErrorBlock message={error} />;
  if (!items) return <LoadingBlock />;
  if (items.length === 0) return <EmptyBlock message="暂无待确认简历。上传 PDF 后会出现在这里。" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">待确认简历</h1>
        <p className="mt-1 text-sm text-muted">未经人工确认的数据不会进入正式候选人看板。</p>
      </div>
      {items.map((resume) => {
        const payload = resume.parsed_payload || {};
        const duplicate = resume.duplicate_candidate;
        return (
          <section key={resume.id} className="rounded-md border border-line bg-white p-5">
            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
              <div>
                <p className="text-sm text-muted">PDF 文件</p>
                <h2 className="text-lg font-semibold text-ink">{resume.filename}</h2>
                <p className="mt-1 text-xs text-muted">SHA256: {resume.sha256.slice(0, 16)}...</p>
              </div>
              <div className="flex gap-2">
                <button className="inline-flex items-center gap-2 rounded-md border border-line px-3 py-2 text-sm" onClick={() => reparse(resume)} disabled={busyId === resume.id}>
                  <RefreshCw size={16} />
                  重新解析
                </button>
                {duplicate ? (
                  <>
                    <button className="inline-flex items-center gap-2 rounded-md border border-brand px-3 py-2 text-sm text-brand" onClick={() => resolveDuplicate(resume, "create")} disabled={busyId === resume.id}>仍然新建候选人</button>
                    <button className="inline-flex items-center gap-2 rounded-md bg-brand px-3 py-2 text-sm text-white" onClick={() => resolveDuplicate(resume, "link")} disabled={busyId === resume.id}><CheckCircle size={16} />关联已有候选人</button>
                  </>
                ) : (
                  <button className="inline-flex items-center gap-2 rounded-md bg-brand px-3 py-2 text-sm text-white" onClick={() => confirm(resume)} disabled={busyId === resume.id}>
                    <CheckCircle size={16} />
                    确认入库
                  </button>
                )}
              </div>
            </div>
            {duplicate ? (
              <div className="mt-4 rounded-md border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                <p className="font-medium">疑似重复候选人：{duplicate.name || `候选人 #${duplicate.id}`}</p>
                <p className="mt-1 text-amber-800">{duplicate.applied_position || "岗位未知"} · {duplicate.school || "学校未知"} · 匹配依据：{resume.duplicate_reason || "姓名及履历信息"}</p>
              </div>
            ) : null}
            <div className="mt-5 grid gap-4 lg:grid-cols-3">
              <div className="rounded-md border border-line p-4">
                <p className="mb-3 text-xs font-medium text-brand">AI 结构化字段</p>
                <dl className="space-y-2 text-sm">
                  <div><dt className="text-muted">姓名</dt><dd>{asText(payload.name) || "-"}</dd></div>
                  <div><dt className="text-muted">岗位</dt><dd>{asText(payload.applied_position) || "-"}</dd></div>
                  <div><dt className="text-muted">学校 / 专业 / 学历</dt><dd>{asText(payload.school) || "-"} / {asText(payload.major) || "-"} / {asText(payload.degree) || "-"}</dd></div>
                  <div><dt className="text-muted">置信度</dt><dd>{String(payload.confidence ?? "-")}</dd></div>
                </dl>
              </div>
              <div className="rounded-md border border-line p-4">
                <p className="mb-3 text-xs font-medium text-brand">AI 摘要与风险</p>
                <p className="text-sm leading-6">{asText(payload.summary) || "暂无摘要"}</p>
                <ul className="mt-3 list-disc pl-5 text-sm text-muted">
                  {asList(payload.risk_points).map((item) => <li key={item}>{item}</li>)}
                </ul>
              </div>
              <div className="rounded-md border border-line p-4">
                <p className="mb-3 text-xs font-medium text-brand">AI 建议面试问题</p>
                <ul className="list-disc pl-5 text-sm text-muted">
                  {asList(payload.interview_questions).map((item) => <li key={item}>{item}</li>)}
                </ul>
              </div>
            </div>
            <details className="mt-4">
              <summary className="cursor-pointer text-sm font-medium text-ink">查看简历原文预览</summary>
              <pre className="mt-3 max-h-72 overflow-auto whitespace-pre-wrap rounded-md bg-panel p-4 text-xs text-slate-700">{resume.extracted_text}</pre>
            </details>
          </section>
        );
      })}
    </div>
  );
}
