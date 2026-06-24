import { ArrowRight, FileText, FolderOpen, Image, Tags } from "lucide-react";
import type { ReactNode } from "react";
import type { Page } from "../App";
import type { Health, ProviderState } from "../types";

export function Dashboard({ health, providers, onNavigate }: { health: Health | null; providers: ProviderState | null; onNavigate: (page: Page) => void }) {
  const backendOnline = Boolean(health);
  const openaiOk = Boolean(providers?.openai.configured);

  return (
    <>
      {/* Hero — ação principal */}
      <div className="dash-hero">
        <div className="dash-hero-body">
          <div className="dash-hero-icon">
            <Image size={22} />
          </div>
          <div className="dash-hero-text">
            <h2 className="dash-hero-title">Criar novo Story</h2>
            <p className="dash-hero-desc">
              Gere um pacote completo de stories para Instagram com IA — escolha a marca, descreva o tema e receba as imagens prontas.
            </p>
          </div>
        </div>
        <button className="dash-hero-btn" onClick={() => onNavigate("stories")}>
          Criar agora <ArrowRight size={16} />
        </button>
      </div>

      {/* Status compacto */}
      <div className="dash-status-strip">
        <div className="dash-status-item">
          <span className={`status-dot ${backendOnline ? "online" : "offline"}`} />
          <span>Backend {backendOnline ? "online" : "offline"}</span>
        </div>
        <div className="dash-status-divider" />
        <div className="dash-status-item">
          <span className={`status-dot ${openaiOk ? "online" : "warning"}`} />
          <span>OpenAI {openaiOk ? "configurada" : "não configurada"}</span>
        </div>
        {openaiOk && providers?.openai && (
          <div className="dash-status-models">
            {providers.openai.text_model  && <span className="dash-model-pill">📝 {providers.openai.text_model}</span>}
            {providers.openai.image_model && <span className="dash-model-pill">🖼 {providers.openai.image_model}</span>}
          </div>
        )}
      </div>

      {/* Ações secundárias */}
      <div className="dash-actions">
        <SecondaryAction
          icon={<Tags size={16} />}
          label="Gerenciar Marcas"
          desc="Importe e edite perfis de marca para personalização automática"
          onClick={() => onNavigate("brands")}
        />
        <SecondaryAction
          icon={<FileText size={16} />}
          label="Gerar Post"
          desc="Crie posts individuais via pipeline de texto e imagem"
          onClick={() => onNavigate("posts")}
        />
        <SecondaryAction
          icon={<FolderOpen size={16} />}
          label="Ver Saídas"
          desc="Acesse os arquivos e imagens gerados anteriormente"
          onClick={() => onNavigate("outputs")}
        />
      </div>
    </>
  );
}

function SecondaryAction({ icon, label, desc, onClick }: { icon: ReactNode; label: string; desc: string; onClick: () => void }) {
  return (
    <button className="dash-action" onClick={onClick}>
      <span className="dash-action-icon">{icon}</span>
      <span className="dash-action-label">{label}</span>
      <span className="dash-action-desc">{desc}</span>
    </button>
  );
}
