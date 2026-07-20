"use client";

import Link from "next/link";
import { ChangeEvent, DragEvent, useState } from "react";
import { CheckCircle2, FileText, ShieldCheck, Upload, X } from "lucide-react";
import { apiPost } from "@/lib/api";
import type { ResumeFile } from "@/lib/types";

const MAX_BYTES = 10 * 1024 * 1024;

export function UploadClient() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ResumeFile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [dragging, setDragging] = useState(false);

  function chooseFile(nextFile: File | null) {
    setResult(null); setError(null);
    if (!nextFile) { setFile(null); return; }
    if (nextFile.type !== "application/pdf" && !nextFile.name.toLowerCase().endsWith(".pdf")) { setFile(null); setError("请选择 PDF 文件。"); return; }
    if (nextFile.size > MAX_BYTES) { setFile(null); setError("PDF 不能超过 10 MB。"); return; }
    setFile(nextFile);
  }

  function onInput(event: ChangeEvent<HTMLInputElement>) { chooseFile(event.target.files?.[0] || null); }
  function onDrop(event: DragEvent<HTMLLabelElement>) { event.preventDefault(); setDragging(false); chooseFile(event.dataTransfer.files?.[0] || null); }

  async function submit() {
    if (!file) return;
    setLoading(true); setError(null);
    const form = new FormData(); form.append("file", file);
    try { setResult(await apiPost<ResumeFile>("/api/resumes/upload", form)); }
    catch (reason) { setError((reason as Error).message); }
    finally { setLoading(false); }
  }

  return <div className="space-y-6">
    <div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand">Resume ingestion</p><h1 className="mt-1 text-2xl font-semibold text-ink">AI 简历录入</h1><p className="mt-1 text-sm text-muted">上传 HR 已获授权的 PDF，系统保存原文件、提取文本并生成待人工确认记录。</p></div>
    <div className="grid gap-5 lg:grid-cols-[1fr_320px]">
      <section className="rounded-xl border border-line bg-white p-5 shadow-sm">
        <label onDragOver={(event) => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={onDrop} className={`flex min-h-64 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 text-center transition-colors ${dragging ? "border-brand bg-blue-50" : "border-slate-300 bg-slate-50 hover:border-brand hover:bg-blue-50/40"}`}>
          <input className="sr-only" type="file" accept="application/pdf,.pdf" onChange={onInput} />
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-100 text-brand"><Upload size={25} /></div><h2 className="mt-4 font-semibold text-ink">拖入 PDF，或点击选择文件</h2><p className="mt-2 text-sm text-muted">仅支持可提取文字的 PDF，单个文件最大 10 MB</p>
        </label>
        {file ? <div className="mt-4 flex items-center gap-3 rounded-lg border border-line p-3"><div className="flex h-10 w-10 items-center justify-center rounded-lg bg-rose-50 text-rose-600"><FileText size={20} /></div><div className="min-w-0 flex-1"><p className="truncate text-sm font-medium text-ink">{file.name}</p><p className="text-xs text-muted">{(file.size / 1024).toFixed(1)} KB · PDF</p></div><button className="rounded-md p-1 text-slate-400 hover:bg-slate-100" onClick={() => chooseFile(null)} aria-label="移除文件"><X size={18} /></button></div> : null}
        <button className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-lg bg-brand px-4 py-3 text-sm font-medium text-white disabled:bg-slate-300" onClick={submit} disabled={!file || loading}><Upload size={17} />{loading ? "正在保存并调用 AI 解析…" : "上传并解析"}</button>
        {error ? <p className="mt-4 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p> : null}
        {result ? <div className="mt-4 rounded-lg border border-emerald-200 bg-emerald-50 p-4"><div className="flex items-center gap-2 font-medium text-emerald-800"><CheckCircle2 size={18} />PDF 已保存并完成解析</div><p className="mt-2 text-sm text-emerald-700">{result.filename} · 状态：{result.parse_status}</p><p className="mt-1 break-all font-mono text-xs text-emerald-700">SHA-256：{result.sha256}</p><Link href="/pending" className="mt-3 inline-block rounded-md bg-emerald-700 px-3 py-2 text-sm text-white">前往人工确认</Link></div> : null}
      </section>
      <aside className="space-y-3"><div className="rounded-xl border border-line bg-white p-5 shadow-sm"><h2 className="flex items-center gap-2 font-semibold text-ink"><ShieldCheck size={18} className="text-brand" />上传后发生什么</h2><ol className="mt-4 space-y-4 text-sm text-muted">{["文件写入后端 data/uploads，不覆盖同名文件", "校验 PDF 文件头并提取原文", "使用当前设置的 AI 模型结构化解析", "进入待确认区，HR 核实后才创建候选人"].map((item, index) => <li key={item} className="flex gap-3"><span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-blue-50 text-xs font-semibold text-brand">{index + 1}</span><span>{item}</span></li>)}</ol></div><div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">请勿上传未经授权的真实候选人简历。Demo 建议使用项目提供的虚构 PDF。</div></aside>
    </div>
  </div>;
}
