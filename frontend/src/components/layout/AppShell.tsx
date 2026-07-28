import type { ReactNode } from "react";
import type { Page } from "../../App";
import type { Health, ProviderState } from "../../types";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

export function AppShell({
  children,
  page,
  setPage,
  health,
  providers,
  brave,
  refreshing,
  onRefresh,
}: {
  children: ReactNode;
  page: Page;
  setPage: (page: Page) => void;
  health: Health | null;
  providers: ProviderState | null;
  brave: string;
  refreshing: boolean;
  onRefresh: () => void;
}) {
  return (
    <div className="app-shell">
      <Sidebar page={page} setPage={setPage} />
      <main className="main">
        <Topbar
          page={page}
          health={health}
          providers={providers}
          brave={brave}
          refreshing={refreshing}
          onRefresh={onRefresh}
        />
        <div className="content">{children}</div>
      </main>
    </div>
  );
}
