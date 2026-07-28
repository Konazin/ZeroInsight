import type { ProviderState } from "../../types";

export function ProviderSettings({ providers }: { providers: ProviderState | null }) {
  if (!providers) {
    return (
      <section className="panel">
        <h2>Providers ativos</h2>
        <div className="empty-state">Carregando providers...</div>
      </section>
    );
  }

  const availableText = providers.available["text"] ?? [];
  const availableImage = providers.available["image"] ?? [];

  return (
    <section className="panel">
      <h2>Providers ativos</h2>
      <div className="grid three" style={{ marginBottom: 16 }}>
        <div className="mini-card">
          Texto
          <strong>{providers.active.text}</strong>
        </div>
        <div className="mini-card">
          Imagem
          <strong>{providers.active.image}</strong>
        </div>
        <div className="mini-card">
          OpenAI
          <strong style={{ color: providers.openai.configured ? "var(--text-primary)" : "var(--text-muted)" }}>
            {providers.openai.configured ? "Configurada" : "Pendente"}
          </strong>
        </div>
      </div>

      {providers.openai.configured && (
        <div style={{ marginBottom: 16 }}>
          <p style={{ margin: "0 0 8px", fontSize: 13, color: "var(--text-subtle)" }}>Modelos OpenAI</p>
          <div className="grid two">
            <div className="mini-card">Texto<strong style={{ fontSize: 13 }}>{providers.openai.text_model}</strong></div>
            <div className="mini-card">Imagem<strong style={{ fontSize: 13 }}>{providers.openai.image_model} ({providers.openai.image_size})</strong></div>
          </div>
        </div>
      )}

      {availableText.length > 0 && (
        <div>
          <p style={{ margin: "0 0 8px", fontSize: 13, color: "var(--text-subtle)" }}>Disponíveis</p>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
            {availableText.map((p) => <span key={p} className="provider-badge">{p}</span>)}
            {availableImage.filter((p) => !availableText.includes(p)).map((p) => <span key={p} className="provider-badge">{p} (img)</span>)}
          </div>
        </div>
      )}
    </section>
  );
}
