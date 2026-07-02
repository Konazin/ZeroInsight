import type { Health, ProviderState } from "../../types";
import { ProviderBadge } from "../common/ProviderBadge";

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

export function Topbar({ health, providers, brave }: { health: Health | null; providers: ProviderState | null; brave: string }) {
  const backendOnline = Boolean(health);
  const braveOnline = brave === "CDP ok";

  return (
    <header className="topbar">
      <div className="topbar-left">
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
      </div>
    </header>
  );
}
