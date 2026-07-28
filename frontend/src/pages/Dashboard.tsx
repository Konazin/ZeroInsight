import { AlertTriangle, ArrowRight, FileText, FolderOpen, Image, Settings, Tags } from "lucide-react";
import type { ReactNode } from "react";
import type { Page } from "../App";
import type { Health, ProviderState } from "../types";

export function Dashboard({ health, providers, onNavigate }: { health: Health | null; providers: ProviderState | null; onNavigate: (page: Page) => void }) {
  const backendOnline = Boolean(health);
  const openaiOk = Boolean(providers?.openai.configured);
  const setupRequired = providers !== null && !openaiOk;

  return (
    <>
      {/* Aviso guiado — só aparece quando algo precisa de atenção */}
      {setupRequired && (
        <button className="dash-setup-banner" onClick={() => onNavigate("settings")}>
          <span className="dash-setup-icon"><AlertTriangle size={16} /></span>
          <span className="dash-setup-text">
            <strong>Configure sua chave OpenAI para gerar imagens reais.</strong>
            <span>Sem a chave, apenas o modo Mock (gradiente local) fica disponível.</span>
          </span>
          <span className="dash-setup-cta">
            <Settings size={14} /> Configurar <ArrowRight size={14} />
          </span>
        </button>
      )}

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
        {openaiOk ? (
          <div className="dash-status-item">
            <span className="status-dot online" />
            <span>OpenAI configurada</span>
          </div>
        ) : (
          <button className="dash-status-item dash-status-item-action" onClick={() => onNavigate("settings")} title="Abrir configurações">
            <span className="status-dot warning" />
            <span>OpenAI não configurada</span>
            <ArrowRight size={12} />
          </button>
        )}
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
