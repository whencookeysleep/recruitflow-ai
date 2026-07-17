"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { LayoutGrid, Table2 } from "lucide-react";
import { apiGet, maskEmail, maskPhone } from "@/lib/api";
import { recruitmentStages, StageBadge, stageClassName } from "@/lib/stages";
import type { Candidate } from "@/lib/types";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "./StateBlock";

const kanbanStages = recruitmentStages.filter((stage) =>
  ["待用人部门二筛", "二筛通过", "待约面试", "已约面试", "待面试反馈", "Offer 待审批", "Offer 已发放"].includes(stage)
);

export function CandidatesClient() {
  const [items, setItems] = useState<Candidate[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<"table" | "kanban">("table");
  const [query, setQuery] = useState("");

  useEffect(() => {
    apiGet<Candidate[]>("/api/candidates")
      .then(setItems)
      .catch((reason: Error) => setError(reason.message));
  }, []);

  const filtered = useMemo(() => {
    if (!items) return [];
    const keyword = query.trim().toLowerCase();
    if (!keyword) return items;
    return items.filter((item) =>
      [item.name, item.school, item.applied_position, item.hr_owner].some((value) => value?.toLowerCase().includes(keyword))
    );
  }, [items, query]);

  if (error) return <ErrorBlock message={error} />;
  if (!items) return <LoadingBlock />;

  return (
    <div className="space-y-5">
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-ink">候选人管理</h1>
          <p className="mt-1 text-sm text-muted">联系方式默认脱敏；待确认简历不会出现在正式候选人列表。</p>
        </div>
        <div className="flex gap-2">
          <button className={`rounded-md border px-3 py-2 text-sm ${view === "table" ? "border-brand text-brand" : "border-line"}`} onClick={() => setView("table")}>
            <Table2 className="inline" size={16} /> 表格
          </button>
          <button className={`rounded-md border px-3 py-2 text-sm ${view === "kanban" ? "border-brand text-brand" : "border-line"}`} onClick={() => setView("kanban")}>
            <LayoutGrid className="inline" size={16} /> 看板
          </button>
        </div>
      </div>
      <input
        className="w-full rounded-md border border-line bg-white px-3 py-2 text-sm"
        placeholder="搜索姓名、学校、岗位或负责人"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
      />
      {filtered.length === 0 ? (
        <EmptyBlock message="暂无候选人数据。可先运行种子脚本或上传确认简历。" />
      ) : view === "table" ? (
        <CandidateTable items={filtered} />
      ) : (
        <Kanban items={filtered} />
      )}
    </div>
  );
}

function CandidateTable({ items }: { items: Candidate[] }) {
  return (
    <div className="overflow-hidden rounded-md border border-line bg-white">
      <table className="w-full min-w-[920px] border-collapse text-sm">
        <thead className="bg-panel text-left text-muted">
          <tr>
            <th className="px-4 py-3">候选人</th>
            <th className="px-4 py-3">联系方式</th>
            <th className="px-4 py-3">岗位</th>
            <th className="px-4 py-3">学校 / 专业</th>
            <th className="px-4 py-3">阶段</th>
            <th className="px-4 py-3">负责人</th>
            <th className="px-4 py-3">详情</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className="border-t border-line">
              <td className="px-4 py-3 font-medium text-ink">{item.name || "-"}</td>
              <td className="px-4 py-3 text-muted">
                {maskPhone(item.phone)}
                <br />
                {maskEmail(item.email)}
              </td>
              <td className="px-4 py-3">{item.applied_position || "-"}</td>
              <td className="px-4 py-3">
                {item.school || "-"} / {item.major || "-"}
              </td>
              <td className="px-4 py-3">
                <StageBadge stage={item.current_stage} />
              </td>
              <td className="px-4 py-3">{item.hr_owner || "-"}</td>
              <td className="px-4 py-3">
                <Link className="text-brand" href={`/candidates/${item.id}`}>
                  查看
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Kanban({ items }: { items: Candidate[] }) {
  return (
    <div className="grid gap-3 xl:grid-cols-3">
      {kanbanStages.map((stage) => {
        const stageItems = items.filter((item) => item.current_stage === stage);
        return (
          <section key={stage} className={`min-h-64 rounded-md border bg-white p-3 ${stageClassName(stage)}`}>
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-sm font-semibold">{stage}</h2>
              <span className="rounded-full bg-white/70 px-2 py-0.5 text-xs">{stageItems.length}</span>
            </div>
            <div className="space-y-2">
              {stageItems.map((item) => (
                <Link key={item.id} href={`/candidates/${item.id}`} className="block rounded-md border border-white/70 bg-white p-3 text-ink hover:border-brand">
                  <p className="font-medium">{item.name || "-"}</p>
                  <p className="mt-1 text-xs text-muted">
                    {item.applied_position || "-"} · {item.school || "-"}
                  </p>
                  {item.is_overdue ? <p className="mt-2 text-xs text-danger">超时未推进</p> : null}
                </Link>
              ))}
            </div>
          </section>
        );
      })}
    </div>
  );
}
