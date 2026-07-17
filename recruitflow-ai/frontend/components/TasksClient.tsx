"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { StageBadge } from "@/lib/stages";
import type { Task } from "@/lib/types";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "./StateBlock";

export function TasksClient() {
  const [tasks, setTasks] = useState<Task[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<Task[]>("/api/tasks")
      .then(setTasks)
      .catch((reason: Error) => setError(reason.message));
  }, []);

  if (error) return <ErrorBlock message={error} />;
  if (!tasks) return <LoadingBlock />;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold text-ink">智能待办</h1>
        <p className="mt-1 text-sm text-muted">超时判断由确定性规则完成；催办文案可直接用于企业微信群。</p>
      </div>
      {tasks.length === 0 ? (
        <EmptyBlock message="暂无超时待办。" />
      ) : (
        <div className="grid gap-3 lg:grid-cols-2">
          {tasks.map((task) => (
            <section key={task.candidate_id} className="rounded-md border border-line bg-white p-5">
              <div className="flex flex-wrap items-center gap-2">
                <p className="text-sm font-semibold text-ink">{task.candidate_name || "候选人"}</p>
                <StageBadge stage={task.stage} />
              </div>
              <p className="mt-2 text-sm text-danger">已超时 {task.overdue_hours} 小时</p>
              <p className="mt-3 rounded-md bg-panel p-3 text-sm text-slate-700">{task.reminder_text}</p>
              <p className="mt-2 text-xs text-muted">待催办部门：{task.department || "未填写"}</p>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
