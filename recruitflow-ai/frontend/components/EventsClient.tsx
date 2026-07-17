"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import type { EventLog } from "@/lib/types";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "./StateBlock";

export function EventsClient() {
  const [events, setEvents] = useState<EventLog[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiGet<EventLog[]>("/api/events")
      .then(setEvents)
      .catch((reason: Error) => setError(reason.message));
  }, []);

  if (error) return <ErrorBlock message={error} />;
  if (!events) return <LoadingBlock />;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold text-ink">招聘事件日志</h1>
        <p className="mt-1 text-sm text-muted">日志记录操作类型、候选人、阶段变化和备注，不输出完整手机号、邮箱或简历正文。</p>
      </div>
      {events.length === 0 ? <EmptyBlock message="暂无事件。" /> : (
        <div className="overflow-hidden rounded-md border border-line bg-white">
          <table className="w-full min-w-[860px] text-left text-sm">
            <thead className="bg-panel text-muted">
              <tr>
                <th className="px-4 py-3">事件类型</th>
                <th className="px-4 py-3">候选人 ID</th>
                <th className="px-4 py-3">操作人</th>
                <th className="px-4 py-3">阶段变化</th>
                <th className="px-4 py-3">时间</th>
                <th className="px-4 py-3">备注</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event) => (
                <tr key={event.id} className="border-t border-line">
                  <td className="px-4 py-3 font-medium text-ink">{event.event_type}</td>
                  <td className="px-4 py-3">{event.candidate_id || "-"}</td>
                  <td className="px-4 py-3">{event.actor}</td>
                  <td className="px-4 py-3">{event.old_stage || "-"} → {event.new_stage || "-"}</td>
                  <td className="px-4 py-3">{new Date(event.created_at).toLocaleString()}</td>
                  <td className="px-4 py-3 text-muted">{event.note || "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
