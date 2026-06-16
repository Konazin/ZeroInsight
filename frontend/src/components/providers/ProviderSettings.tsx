import type { ProviderState } from "../../types";

export function ProviderSettings({ providers }: { providers: ProviderState | null }) {
  return (
    <section className="panel">
      <h2>Providers ativos</h2>
      <div className="grid three">
        <div className="mini-card">Texto<br /><strong>{providers?.active.text ?? "-"}</strong></div>
        <div className="mini-card">Imagem<br /><strong>{providers?.active.image ?? "-"}</strong></div>
        <div className="mini-card">OpenAI<br /><strong>{providers?.openai.configured ? "OK" : "Nao configurada"}</strong></div>
      </div>
    </section>
  );
}
