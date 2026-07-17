import { AppShell } from "@/components/AppShell";
import { TasksClient } from "@/components/TasksClient";

export default function TasksPage() {
  return (
    <AppShell>
      <TasksClient />
    </AppShell>
  );
}
