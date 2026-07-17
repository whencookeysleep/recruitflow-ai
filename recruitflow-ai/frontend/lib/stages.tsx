export const recruitmentStages = [
  "HR 初筛通过",
  "待用人部门二筛",
  "二筛通过",
  "二筛不通过",
  "待约面试",
  "已约面试",
  "面试完成",
  "待面试反馈",
  "面试通过",
  "面试不通过",
  "Offer 待审批",
  "Offer 已发放",
  "已入职",
  "已放弃"
];

const stageClassMap: Record<string, string> = {
  "HR 初筛通过": "border-sky-200 bg-sky-50 text-sky-700",
  "待用人部门二筛": "border-amber-200 bg-amber-50 text-amber-700",
  "二筛通过": "border-emerald-200 bg-emerald-50 text-emerald-700",
  "二筛不通过": "border-rose-200 bg-rose-50 text-rose-700",
  "待约面试": "border-violet-200 bg-violet-50 text-violet-700",
  "已约面试": "border-indigo-200 bg-indigo-50 text-indigo-700",
  "面试完成": "border-cyan-200 bg-cyan-50 text-cyan-700",
  "待面试反馈": "border-orange-200 bg-orange-50 text-orange-700",
  "面试通过": "border-green-200 bg-green-50 text-green-700",
  "面试不通过": "border-red-200 bg-red-50 text-red-700",
  "Offer 待审批": "border-fuchsia-200 bg-fuchsia-50 text-fuchsia-700",
  "Offer 已发放": "border-teal-200 bg-teal-50 text-teal-700",
  "已入职": "border-lime-200 bg-lime-50 text-lime-700",
  "已放弃": "border-slate-200 bg-slate-50 text-slate-600"
};

export function stageClassName(stage: string | null | undefined): string {
  if (!stage) return "border-slate-200 bg-slate-50 text-slate-600";
  return stageClassMap[stage] || "border-slate-200 bg-slate-50 text-slate-600";
}

export function StageBadge({ stage }: { stage: string | null | undefined }) {
  return (
    <span className={`inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium ${stageClassName(stage)}`}>
      {stage || "未设置"}
    </span>
  );
}
