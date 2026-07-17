import { AppShell } from "@/components/AppShell";
import { CandidateDetailClient } from "@/components/CandidateDetailClient";

export default function CandidateDetailPage({ params }: { params: { id: string } }) {
  return (
    <AppShell>
      <CandidateDetailClient id={params.id} />
    </AppShell>
  );
}
