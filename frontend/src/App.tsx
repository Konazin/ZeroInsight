import { useEffect, useState } from "react";
import { AppShell } from "./components/layout/AppShell";
import { Dashboard } from "./pages/Dashboard";
import { Brands } from "./pages/Brands";
import { Providers } from "./pages/Providers";
import { GenerateStories } from "./pages/GenerateStories";
import { GeneratePosts } from "./pages/GeneratePosts";
import { Outputs } from "./pages/Outputs";
import { SettingsPage } from "./pages/Settings";
import { Logs } from "./pages/Logs";
import { api } from "./lib/api";
import type { Health, ProviderState } from "./types";

export type Page = "dashboard" | "brands" | "providers" | "stories" | "posts" | "outputs" | "settings" | "logs";

export function App() {
  const [page, setPage] = useState<Page>("dashboard");
  const [health, setHealth] = useState<Health | null>(null);
  const [providers, setProviders] = useState<ProviderState | null>(null);
  const [brave, setBrave] = useState<string>("verificando");

  useEffect(() => {
    void refreshStatus();
    const id = setInterval(() => void refreshStatus(), 30_000);
    return () => clearInterval(id);
  }, []);

  async function refreshStatus() {
    try {
      const [h, p, b] = await Promise.all([api.health(), api.providers(), api.braveStatus()]);
      setHealth(h);
      setProviders(p);
      setBrave(b.ok ? "CDP ok" : "CDP offline");
    } catch {
      setHealth(null);
      setBrave("backend offline");
    }
  }

  const content = {
    dashboard: <Dashboard providers={providers} health={health} onNavigate={setPage} />,
    brands: <Brands />,
    providers: <Providers providers={providers} onRefresh={refreshStatus} />,
    stories: <GenerateStories />,
    posts: <GeneratePosts />,
    outputs: <Outputs />,
    settings: <SettingsPage onSaved={refreshStatus} />,
    logs: <Logs />,
  }[page];

  return (
    <AppShell page={page} setPage={setPage} health={health} providers={providers} brave={brave}>
      {content}
    </AppShell>
  );
}
