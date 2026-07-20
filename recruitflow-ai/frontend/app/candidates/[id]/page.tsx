import { AppShell } from "@/components/AppShell";
import { CandidateScreeningClient } from "@/components/CandidateScreeningClient";

export default async function CandidateDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <AppShell>
      <CandidateScreeningClient id={id} />
    </AppShell>
  );
}
