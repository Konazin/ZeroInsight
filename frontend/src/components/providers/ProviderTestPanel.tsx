import { useState } from "react";
import { FlaskConical } from "lucide-react";
import { api } from "../../lib/api";

export function ProviderTestPanel() {
  const [kind, setKind] = useState("text");
  const [name, setName] = useState("mock");
  const [status, setStatus] = useState<{ text: string; ok: boolean } | null>(null);
  const [loading, setLoading] = useState(false);

  async function test() {
    if (!name.trim()) return;
    setLoading(true);
    setStatus(null);
    try {
      const response = await api.testProvider(kind, name.trim());
      setStatus({ text: response.message, ok: response.ok });
    } catch (error) {
      setStatus({ text: error instanceof Error ? error.message : "Erro ao testar.", ok: false });
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel">
      <h2>Teste rápido</h2>
      <div className="field">
        <span>Tipo de provider</span>
        <select value={kind} onChange={(event) => setKind(event.target.value)}>
          <option value="text">Texto</option>
          <option value="image">Imagem</option>
          <option value="vision">Visão</option>
        </select>
      </div>
      <div className="field">
        <span>Nome do provider</span>
        <input value={name} onChange={(event) => setName(event.target.value)} placeholder="Ex: mock, openai, groq" />
      </div>
      <button onClick={test} disabled={loading || !name.trim()}>
        <FlaskConical size={16} /> {loading ? "Testando..." : "Testar"}
      </button>
      {status && (
        <p className={`feedback ${status.ok ? "success" : "error"}`} style={{ marginTop: 8, marginBottom: 0 }}>
          {status.text}
        </p>
      )}
    </section>
  );
}
