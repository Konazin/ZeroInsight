import type { Page } from "../App";
import { StatusCard } from "../components/common/StatusCard";
import type { Health, ProviderState } from "../types";

export function Dashboard({ health, providers, onNavigate }: { health: Health | null; providers: ProviderState | null; onNavigate: (page: Page) => void }) {
  return (
    <>
      <div className="grid four">
        <StatusCard title="Backend" value={health ? "Online" : "Offline"} tone={health ? "success" : "danger"} />
        <StatusCard title="OpenAI" value={providers?.openai.configured ? "Configurada" : "Pendente"} tone={providers?.openai.configured ? "success" : "warning"} />
        <StatusCard title="Texto" value={providers?.active.text ?? "-"} />
        <StatusCard title="Imagem" value={providers?.active.image ?? "-"} />
      </div>
      <section className="panel">
        <h1>Dashboard</h1>
        <div className="quick-actions">
          <button onClick={() => onNavigate("brands")}>Importar marca</button>
          <button onClick={() => onNavigate("stories")}>Gerar Story</button>
          <button onClick={() => onNavigate("posts")}>Gerar Post</button>
          <button onClick={() => onNavigate("outputs")}>Abrir saidas</button>
        </div>
      </section>
    </>
  );
}
