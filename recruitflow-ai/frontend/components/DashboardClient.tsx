"use client";

import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { apiGet } from "@/lib/api";
import type { ChartPoint, Metrics, Trends } from "@/lib/types";
import { EmptyBlock, ErrorBlock, LoadingBlock } from "./StateBlock";

const metricLabels: Record<keyof Metrics, string> = {
  total_candidates: "候选人总数",
  new_this_week: "本周新增",
  pending_screening: "待二筛",
  pending_interview_schedule: "待约面试",
  pending_feedback: "待反馈",
  overdue: "超时未推进",
  offers: "Offer 人数"
};

function ChartPanel({ title, data, type = "bar" }: { title: string; data: ChartPoint[]; type?: "bar" | "line" }) {
  return (
    <section className="rounded-md border border-line bg-white p-4">
      <h2 className="mb-4 text-base font-semibold text-ink">{title}</h2>
      {data.length === 0 ? (
        <EmptyBlock message="暂无数据" />
      ) : (
        <div className="h-72">
          <ResponsiveContainer width="100%" height="100%">
            {type === "bar" ? (
              <BarChart data={data}>
                <CartesianGrid stroke="#edf2f7" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="value" fill="#1f6feb" radius={[4, 4, 0, 0]} />
              </BarChart>
            ) : (
              <LineChart data={data}>
                <CartesianGrid stroke="#edf2f7" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis />
                <Tooltip />
                <Line type="monotone" dataKey="value" stroke="#1f6feb" strokeWidth={2} dot={false} />
              </LineChart>
            )}
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}

export function DashboardClient() {
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [funnel, setFunnel] = useState<ChartPoint[]>([]);
  const [trends, setTrends] = useState<Trends | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      apiGet<Metrics>("/api/dashboard/metrics"),
      apiGet<ChartPoint[]>("/api/dashboard/funnel"),
      apiGet<Trends>("/api/dashboard/trends")
    ])
      .then(([nextMetrics, nextFunnel, nextTrends]) => {
        setMetrics(nextMetrics);
        setFunnel(nextFunnel);
        setTrends(nextTrends);
      })
      .catch((reason: Error) => setError(reason.message));
  }, []);

  if (error) return <ErrorBlock message={error} />;
  if (!metrics || !trends) return <LoadingBlock />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">招聘数据看板</h1>
        <p className="mt-1 text-sm text-muted">所有指标来自数据库实时查询，状态流转和超时判断不调用 AI。</p>
      </div>
      <section className="grid gap-3 md:grid-cols-2 xl:grid-cols-7">
        {(Object.keys(metricLabels) as Array<keyof Metrics>).map((key) => (
          <div key={key} className="rounded-md border border-line bg-white p-4">
            <p className="text-xs text-muted">{metricLabels[key]}</p>
            <p className="mt-2 text-2xl font-semibold text-ink">{metrics[key]}</p>
          </div>
        ))}
      </section>
      <section className="grid gap-4 xl:grid-cols-2">
        <ChartPanel title="招聘阶段漏斗" data={funnel} />
        <ChartPanel title="最近七天新增候选人趋势" data={trends.recent_seven_days} type="line" />
        <ChartPanel title="各岗位候选人数" data={trends.position_counts} />
        <ChartPanel title="各招聘环节平均停留时间（小时）" data={trends.average_stage_hours} />
      </section>
    </div>
  );
}
