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

const PAGES: Page[] = ["dashboard", "brands", "providers", "stories", "posts", "outputs", "settings", "logs"];

function initialPage(): Page {
  const hash = window.location.hash.replace("#/", "") as Page;
  return PAGES.includes(hash) ? hash : "dashboard";
}

export function App() {
  const [page, setPage] = useState<Page>(initialPage);
  const [health, setHealth] = useState<Health | null>(null);
  const [providers, setProviders] = useState<ProviderState | null>(null);
  const [brave, setBrave] = useState<string>("verificando");
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    void refreshStatus();
    const id = setInterval(() => void refreshStatus(), 30_000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const onHashChange = () => setPage(initialPage());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  useEffect(() => {
    window.location.hash = `/${page}`;
    window.scrollTo({ top: 0 });
  }, [page]);

  async function refreshStatus() {
    setRefreshing(true);
    try {
      const [h, p, b] = await Promise.all([api.health(), api.providers(), api.braveStatus()]);
      setHealth(h);
      setProviders(p);
      setBrave(b.ok ? "CDP ok" : "CDP offline");
    } catch {
      setHealth(null);
      setProviders(null);
      setBrave("backend offline");
    } finally {
      setRefreshing(false);
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
    <AppShell
      page={page}
      setPage={setPage}
      health={health}
      providers={providers}
      brave={brave}
      refreshing={refreshing}
      onRefresh={refreshStatus}
    >
      {content}
    </AppShell>
  );
}
