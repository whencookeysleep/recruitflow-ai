import { AppShell } from "@/components/AppShell";
import { DashboardClient } from "@/components/DashboardClient";

export default function HomePage() {
  return (
    <AppShell>
      <DashboardClient />
    </AppShell>
  );
}
