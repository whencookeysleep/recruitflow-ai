"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { ChevronLeft, ChevronRight, LayoutGrid, Search, SlidersHorizontal, Table2 } from "lucide-react";
import { apiGet, maskEmail, maskPhone } from "@/lib/api";
import { recruitmentStages, StageBadge, stageClassName } from "@/lib/stages";
import type { Candidate } from "@/lib/types";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "./StateBlock";

const PAGE_SIZE = 10;
const kanbanStages = recruitmentStages.filter((stage) => ["待用人部门二筛", "二筛通过", "待约面试", "已约面试", "待面试反馈", "Offer 待审批", "Offer 已发放"].includes(stage));

export function CandidatesClient() {
  const [items, setItems] = useState<Candidate[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<"table" | "kanban">("table");
  const [query, setQuery] = useState("");
  const [department, setDepartment] = useState("all");
  const [page, setPage] = useState(1);

  useEffect(() => { apiGet<Candidate[]>("/api/candidates").then(setItems).catch((reason: Error) => setError(reason.message)); }, []);

  const departments = useMemo(() => Array.from(new Set((items || []).map((item) => item.department).filter(Boolean) as string[])).sort(), [items]);
  const filtered = useMemo(() => {
    const keyword = query.trim().toLowerCase();
    return (items || []).filter((item) => {
      const queryMatches = !keyword || [item.name, item.school, item.applied_position, item.department, item.hr_owner].some((value) => value?.toLowerCase().includes(keyword));
      return queryMatches && (department === "all" || item.department === department);
    });
  }, [items, query, department]);
  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageItems = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  if (error) return <ErrorBlock message={error} />;
  if (!items) return <LoadingBlock />;

  function changeFilters(callback: () => void) { callback(); setPage(1); }

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
        <div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand">Talent pool</p><h1 className="mt-1 text-2xl font-semibold text-ink">候选人管理</h1><p className="mt-1 text-sm text-muted">共 {items.length} 位虚构演示候选人，联系方式默认脱敏。</p></div>
        <div className="flex rounded-lg border border-line bg-white p-1">
          <button className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-sm ${view === "table" ? "bg-slate-900 text-white" : "text-slate-600"}`} onClick={() => setView("table")}><Table2 size={16} />表格</button>
          <button className={`flex items-center gap-2 rounded-md px-3 py-1.5 text-sm ${view === "kanban" ? "bg-slate-900 text-white" : "text-slate-600"}`} onClick={() => setView("kanban")}><LayoutGrid size={16} />看板</button>
        </div>
      </div>
      <div className="flex flex-col gap-3 rounded-xl border border-line bg-white p-3 shadow-sm md:flex-row">
        <label className="relative flex-1"><Search className="absolute left-3 top-2.5 text-slate-400" size={18} /><input className="w-full rounded-lg border border-line py-2 pl-10 pr-3 text-sm outline-none focus:border-brand" placeholder="搜索姓名、岗位、学校或负责人" value={query} onChange={(event) => changeFilters(() => setQuery(event.target.value))} /></label>
        <label className="relative md:w-56"><SlidersHorizontal className="absolute left-3 top-2.5 text-slate-400" size={17} /><select className="w-full appearance-none rounded-lg border border-line py-2 pl-10 pr-3 text-sm" value={department} onChange={(event) => changeFilters(() => setDepartment(event.target.value))}><option value="all">全部部门</option>{departments.map((item) => <option key={item}>{item}</option>)}</select></label>
      </div>
      {filtered.length === 0 ? <EmptyBlock message="没有符合当前筛选条件的候选人。" /> : view === "table" ? <CandidateTable items={pageItems} /> : <Kanban items={filtered} />}
      {view === "table" && filtered.length ? <div className="flex items-center justify-between text-sm text-muted"><span>显示 {(page - 1) * PAGE_SIZE + 1}-{Math.min(page * PAGE_SIZE, filtered.length)}，共 {filtered.length} 条</span><div className="flex items-center gap-2"><button disabled={page === 1} className="rounded-md border border-line bg-white p-2 disabled:opacity-40" onClick={() => setPage((value) => value - 1)}><ChevronLeft size={16} /></button><span className="px-2">{page} / {pageCount}</span><button disabled={page === pageCount} className="rounded-md border border-line bg-white p-2 disabled:opacity-40" onClick={() => setPage((value) => value + 1)}><ChevronRight size={16} /></button></div></div> : null}
    </div>
  );
}

function CandidateTable({ items }: { items: Candidate[] }) {
  return <div className="overflow-x-auto rounded-xl border border-line bg-white shadow-sm"><table className="w-full min-w-[1050px] border-collapse text-sm"><thead className="bg-slate-50 text-left text-xs font-medium uppercase tracking-wide text-slate-500"><tr><th className="px-5 py-3">候选人</th><th className="px-4 py-3">目标岗位</th><th className="px-4 py-3">教育背景</th><th className="px-4 py-3">技能标签</th><th className="px-4 py-3">当前阶段</th><th className="px-4 py-3">负责人</th><th className="px-4 py-3 text-right">操作</th></tr></thead><tbody>{items.map((item) => <tr key={item.id} className="border-t border-line align-middle transition-colors hover:bg-blue-50/30"><td className="px-5 py-4"><div className="flex items-center gap-3"><div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-blue-100 to-indigo-100 font-semibold text-brand">{item.name?.slice(0, 1) || "?"}</div><div><p className="font-medium text-ink">{item.name || "-"}</p><p className="mt-0.5 text-xs text-muted">{maskPhone(item.phone)} · {maskEmail(item.email)}</p></div></div></td><td className="px-4 py-4"><p className="font-medium text-ink">{item.applied_position || "-"}</p><p className="mt-0.5 text-xs text-muted">{item.department || "未分配部门"}</p></td><td className="px-4 py-4"><p>{item.school || "-"}</p><p className="mt-0.5 text-xs text-muted">{item.degree || "-"} · {item.major || "-"}</p></td><td className="max-w-[230px] px-4 py-4"><div className="flex flex-wrap gap-1">{item.skills.slice(0, 3).map((skill) => <span key={skill} className="rounded bg-slate-100 px-2 py-1 text-xs text-slate-600">{skill}</span>)}{item.skills.length > 3 ? <span className="rounded bg-slate-100 px-2 py-1 text-xs text-slate-500">+{item.skills.length - 3}</span> : null}</div></td><td className="px-4 py-4"><StageBadge stage={item.current_stage} /></td><td className="px-4 py-4 text-slate-600">{item.hr_owner || "-"}</td><td className="px-4 py-4 text-right"><Link className="rounded-md border border-line px-3 py-1.5 text-sm font-medium text-brand hover:border-brand hover:bg-blue-50" href={`/candidates/${item.id}`}>查看详情</Link></td></tr>)}</tbody></table></div>;
}

function Kanban({ items }: { items: Candidate[] }) {
  return <div className="grid gap-3 xl:grid-cols-3">{kanbanStages.map((stage) => { const stageItems = items.filter((item) => item.current_stage === stage); return <section key={stage} className={`min-h-64 rounded-xl border bg-white p-3 ${stageClassName(stage)}`}><div className="mb-3 flex items-center justify-between"><h2 className="text-sm font-semibold">{stage}</h2><span className="rounded-full bg-white/80 px-2 py-0.5 text-xs">{stageItems.length}</span></div><div className="space-y-2">{stageItems.map((item) => <Link key={item.id} href={`/candidates/${item.id}`} className="block rounded-lg border border-white/70 bg-white p-3 text-ink shadow-sm hover:border-brand"><p className="font-medium">{item.name || "-"}</p><p className="mt-1 text-xs text-muted">{item.applied_position || "-"} · {item.school || "-"}</p>{item.is_overdue ? <p className="mt-2 text-xs text-danger">超时未推进</p> : null}</Link>)}</div></section>; })}</div>;
}
