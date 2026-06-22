import { useEffect, useState } from "react";
import { Save } from "lucide-react";
import { api } from "../../lib/api";
import type { Settings } from "../../types";

type FieldMeta = { label: string; placeholder?: string; type?: string };

const GROUPS: Array<{ title: string; fields: Record<string, FieldMeta> }> = [
  {
    title: "Chaves de API",
    fields: {
      openai_api_key: { label: "OpenAI", placeholder: "sk-...", type: "password" },
      groq_api_key: { label: "Groq", placeholder: "gsk_...", type: "password" },
    },
  },
  {
    title: "Modelos",
    fields: {
      openai_text_model: { label: "Texto (OpenAI)", placeholder: "gpt-4o" },
      openai_image_model: { label: "Imagem (OpenAI)", placeholder: "dall-e-3" },
      openai_vision_model: { label: "Visão (OpenAI)", placeholder: "gpt-4o" },
    },
  },
  {
    title: "Provedores padrão",
    fields: {
      default_text_provider: { label: "Texto", placeholder: "openai, groq, mock..." },
      default_image_provider: { label: "Imagem", placeholder: "openai, stability, mock..." },
      default_vision_provider: { label: "Visão", placeholder: "openai, mock..." },
    },
  },
];

export function SettingsPanel({ onSaved }: { onSaved: () => void }) {
  const [settings, setSettings] = useState<Settings>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<{ text: string; kind: "success" | "error" } | null>(null);

  useEffect(() => {
    void api.settings().then((s) => { setSettings(s); setLoading(false); });
  }, []);

  function update(key: string, value: string) {
    setSettings((current) => ({ ...current, [key]: value }));
    setStatus(null);
  }

  async function save() {
    setSaving(true);
    setStatus(null);
    try {
      await api.saveSettings(settings);
      setStatus({ text: "Configurações salvas com sucesso.", kind: "success" });
      onSaved();
    } catch (error) {
      setStatus({ text: error instanceof Error ? error.message : "Falha ao salvar.", kind: "error" });
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return <section className="panel"><h2>Configurações</h2><div className="loading-state">Carregando...</div></section>;
  }

  return (
    <section className="panel">
      <h2>Configurações</h2>
      {GROUPS.map((group) => (
        <div key={group.title} className="settings-section">
          <p className="settings-section-title">{group.title}</p>
          <div className="grid two" style={{ gap: 12 }}>
            {Object.entries(group.fields).map(([key, meta]) => (
              <label key={key} className="field" style={{ marginBottom: 0 }}>
                <span>{meta.label}</span>
                <input
                  type={meta.type ?? "text"}
                  value={String(settings[key] ?? "")}
                  onChange={(e) => update(key, e.target.value)}
                  placeholder={meta.placeholder}
                />
              </label>
            ))}
          </div>
        </div>
      ))}
      <button onClick={save} disabled={saving}>
        <Save size={16} /> {saving ? "Salvando..." : "Salvar configurações"}
      </button>
      {status && <p className={`feedback ${status.kind}`} style={{ marginBottom: 0 }}>{status.text}</p>}
    </section>
  );
}
