"use client";

import { useState } from "react";
import { Upload } from "lucide-react";
import { apiPost } from "@/lib/api";
import type { ResumeFile } from "@/lib/types";

export function UploadClient() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ResumeFile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    if (!file) return;
    setLoading(true);
    setError(null);
    const form = new FormData();
    form.append("file", file);
    try {
      setResult(await apiPost<ResumeFile>("/api/resumes/upload", form));
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">AI 简历录入</h1>
        <p className="mt-1 text-sm text-muted">上传 HR 已授权下载的 PDF。AI 只做结构化解析，结果必须进入人工确认。</p>
      </div>
      <section className="rounded-md border border-line bg-white p-5">
        <label className="block text-sm font-medium text-ink">选择 PDF 简历</label>
        <input
          className="mt-3 block w-full rounded-md border border-line p-3 text-sm"
          type="file"
          accept="application/pdf"
          onChange={(event) => setFile(event.target.files?.[0] || null)}
        />
        <button
          className="mt-4 inline-flex items-center gap-2 rounded-md bg-brand px-4 py-2 text-sm font-medium text-white disabled:bg-slate-300"
          onClick={submit}
          disabled={!file || loading}
        >
          <Upload size={16} />
          {loading ? "解析中..." : "上传并解析"}
        </button>
        {error ? <p className="mt-4 text-sm text-danger">{error}</p> : null}
        {result ? (
          <div className="mt-5 rounded-md border border-blue-200 bg-blue-50 p-4 text-sm">
            <p className="font-medium text-ink">已生成待确认记录：{result.filename}</p>
            <p className="mt-1 text-muted">状态：{result.parse_status}；置信度和 AI 摘要请到“待确认简历”页面确认。</p>
          </div>
        ) : null}
      </section>
    </div>
  );
}
