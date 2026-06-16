import type { Health, ProviderState } from "../../types";
import { ProviderBadge } from "../common/ProviderBadge";

export function Topbar({ health, providers, brave }: { health: Health | null; providers: ProviderState | null; brave: string }) {
  return (
    <header className="topbar">
      <div>
        <strong>{health ? "Backend online" : "Backend offline"}</strong>
        <span>{brave}</span>
      </div>
      <div className="topbar-actions">
        <ProviderBadge label="Texto" value={providers?.active.text ?? "-"} />
        <ProviderBadge label="Imagem" value={providers?.active.image ?? "-"} />
      </div>
    </header>
  );
}
