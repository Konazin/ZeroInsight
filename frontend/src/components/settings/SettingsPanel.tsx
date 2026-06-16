import { useEffect, useState } from "react";
import { Save } from "lucide-react";
import { api } from "../../lib/api";
import type { Settings } from "../../types";

export function SettingsPanel({ onSaved }: { onSaved: () => void }) {
  const [settings, setSettings] = useState<Settings>({});
  const [status, setStatus] = useState("");

  useEffect(() => { void api.settings().then(setSettings); }, []);

  function update(key: string, value: string) {
    setSettings((current) => ({ ...current, [key]: value }));
  }

  async function save() {
    await api.saveSettings(settings);
    setStatus("Configuracoes salvas.");
    onSaved();
  }

  return (
    <section className="panel">
      <h2>Configuracoes</h2>
      {["openai_api_key", "openai_text_model", "openai_image_model", "default_text_provider", "default_image_provider"].map((key) => (
        <label key={key} className="field"><span>{key}</span><input value={String(settings[key] ?? "")} onChange={(event) => update(key, event.target.value)} /></label>
      ))}
      <button onClick={save}><Save size={16} /> Salvar</button>
      <small>{status}</small>
    </section>
  );
}
