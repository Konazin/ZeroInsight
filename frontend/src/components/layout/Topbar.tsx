import type { Health, ProviderState } from "../../types";
import { ProviderBadge } from "../common/ProviderBadge";
import { RefreshCw } from "lucide-react";
import type { Page } from "../../App";

const PAGE_META: Record<Page, { title: string; eyebrow: string }> = {
  dashboard: { title: "Visão geral", eyebrow: "Workspace" },
  stories: { title: "Criar stories", eyebrow: "Criação" },
  posts: { title: "Criar posts", eyebrow: "Criação" },
  brands: { title: "Marcas", eyebrow: "Biblioteca" },
  outputs: { title: "Arquivos gerados", eyebrow: "Biblioteca" },
  providers: { title: "IA e providers", eyebrow: "Sistema" },
  settings: { title: "Configurações", eyebrow: "Sistema" },
  logs: { title: "Logs do sistema", eyebrow: "Sistema" },
};

function StatusIndicator({
  dot,
  label,
  sublabel,
  title,
}: {
  dot: "online" | "offline" | "warning" | "neutral";
  label: string;
  sublabel?: string;
  title?: string;
}) {
  return (
    <div className="topbar-status" title={title}>
      <span className={`status-dot ${dot}`} />
      <span style={{ color: "var(--text-primary)" }}>{label}</span>
      {sublabel && <span style={{ color: "var(--text-subtle)", fontSize: 12 }}>{sublabel}</span>}
    </div>
  );
}

export function Topbar({
  page,
  health,
  providers,
  brave,
  refreshing,
  onRefresh,
}: {
  page: Page;
  health: Health | null;
  providers: ProviderState | null;
  brave: string;
  refreshing: boolean;
  onRefresh: () => void;
}) {
  const backendOnline = Boolean(health);
  const braveOnline = brave === "CDP ok";
  const meta = PAGE_META[page];

  return (
    <header className="topbar">
      <div className="topbar-left">
        <div className="topbar-page">
          <span>{meta.eyebrow}</span>
          <strong>{meta.title}</strong>
        </div>
        <div className="topbar-separator" />
        <StatusIndicator
          dot={backendOnline ? "online" : "offline"}
          label={backendOnline ? "Backend online" : "Backend offline"}
          title={backendOnline ? "Servidor local respondendo normalmente" : "O servidor local não está respondendo"}
        />
        {/* Integração opcional — só destacamos quando conectada; caso contrário fica discreta */}
        <StatusIndicator
          dot={braveOnline ? "online" : "neutral"}
          label="Brave"
          sublabel={braveOnline ? "conectado" : "opcional"}
          title="Integração opcional com o Brave (métricas Dino via CDP). Não é necessária para gerar stories."
        />
      </div>
      <div className="topbar-actions">
        <ProviderBadge label="Texto" value={providers?.active.text ?? "-"} />
        <ProviderBadge label="Imagem" value={providers?.active.image ?? "-"} />
        <button
          className="btn-icon"
          onClick={onRefresh}
          disabled={refreshing}
          title="Atualizar status"
          aria-label="Atualizar status do sistema"
        >
          <RefreshCw size={15} className={refreshing ? "is-spinning" : ""} />
        </button>
      </div>
    </header>
  );
}
