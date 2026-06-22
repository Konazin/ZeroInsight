import type { ReactNode } from "react";
import { Tags, Image, FileText, FolderOpen } from "lucide-react";
import type { Page } from "../App";
import { StatusCard } from "../components/common/StatusCard";
import type { Health, ProviderState } from "../types";

export function Dashboard({ health, providers, onNavigate }: { health: Health | null; providers: ProviderState | null; onNavigate: (page: Page) => void }) {
  const backendTone = health ? "success" : "danger";
  const openaiTone = providers?.openai.configured ? "success" : "warning";

  return (
    <>
      <div className="grid four">
        <StatusCard title="Backend" value={health ? "Online" : "Offline"} tone={backendTone} />
        <StatusCard title="OpenAI" value={providers?.openai.configured ? "Configurada" : "Pendente"} tone={openaiTone} />
        <StatusCard title="Provedor de Texto" value={providers?.active.text ?? "-"} />
        <StatusCard title="Provedor de Imagem" value={providers?.active.image ?? "-"} />
      </div>

      <section className="panel">
        <div className="section-header">
          <h2>Ações rápidas</h2>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 10 }}>
          <QuickAction icon={<Tags size={18} />} label="Importar marca" desc="Adicionar PDF ou DOCX de marca" onClick={() => onNavigate("brands")} />
          <QuickAction icon={<Image size={18} />} label="Gerar Story" desc="Criar pacote de stories para Instagram" onClick={() => onNavigate("stories")} />
          <QuickAction icon={<FileText size={18} />} label="Gerar Post" desc="Gerar post jurídico via pipeline" onClick={() => onNavigate("posts")} />
          <QuickAction icon={<FolderOpen size={18} />} label="Ver saídas" desc="Visualizar arquivos gerados" onClick={() => onNavigate("outputs")} />
        </div>
      </section>

      {providers?.openai.configured && (
        <section className="panel">
          <div className="section-header"><h2>Modelos OpenAI ativos</h2></div>
          <div className="grid three">
            <div className="mini-card">Texto<strong>{providers.openai.text_model || "-"}</strong></div>
            <div className="mini-card">Imagem<strong>{providers.openai.image_model || "-"} ({providers.openai.image_size})</strong></div>
            <div className="mini-card">Raciocínio<strong>{providers.openai.reasoning_model || "-"}</strong></div>
          </div>
        </section>
      )}
    </>
  );
}

function QuickAction({ icon, label, desc, onClick }: { icon: ReactNode; label: string; desc: string; onClick: () => void }) {
  return (
    <button className="quick-action" onClick={onClick}>
      <span className="quick-action-icon">{icon}</span>
      <span className="quick-action-body">
        <span className="quick-action-label">{label}</span>
        <span className="quick-action-desc">{desc}</span>
      </span>
    </button>
  );
}
