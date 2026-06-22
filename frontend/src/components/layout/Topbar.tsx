import type { Health, ProviderState } from "../../types";
import { ProviderBadge } from "../common/ProviderBadge";

function StatusIndicator({ online, label, sublabel }: { online: boolean | null; label: string; sublabel?: string }) {
  const dotClass = online === null ? "neutral" : online ? "online" : "offline";
  return (
    <div className="topbar-status">
      <span className={`status-dot ${dotClass}`} />
      <span style={{ color: "#f9fafb" }}>{label}</span>
      {sublabel && <span style={{ color: "#64748b", fontSize: 12 }}>{sublabel}</span>}
    </div>
  );
}

export function Topbar({ health, providers, brave }: { health: Health | null; providers: ProviderState | null; brave: string }) {
  const braveOnline = brave === "CDP ok";
  const braveOffline = brave === "CDP offline" || brave === "backend offline";

  return (
    <header className="topbar">
      <div className="topbar-left">
        <StatusIndicator online={health ? true : false} label={health ? "Backend online" : "Backend offline"} />
        <StatusIndicator
          online={braveOffline ? false : braveOnline ? true : null}
          label={brave}
        />
      </div>
      <div className="topbar-actions">
        <ProviderBadge label="Texto" value={providers?.active.text ?? "-"} />
        <ProviderBadge label="Imagem" value={providers?.active.image ?? "-"} />
      </div>
    </header>
  );
}
