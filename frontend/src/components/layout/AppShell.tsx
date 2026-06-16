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
}: {
  children: ReactNode;
  page: Page;
  setPage: (page: Page) => void;
  health: Health | null;
  providers: ProviderState | null;
  brave: string;
}) {
  return (
    <div className="app-shell">
      <Sidebar page={page} setPage={setPage} />
      <main className="main">
        <Topbar health={health} providers={providers} brave={brave} />
        <div className="content">{children}</div>
      </main>
    </div>
  );
}
