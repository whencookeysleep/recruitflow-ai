import { AppShell } from "@/components/AppShell";
import { PendingResumesClient } from "@/components/PendingResumesClient";

export default function PendingPage() {
  return (
    <AppShell>
      <PendingResumesClient />
    </AppShell>
  );
}
