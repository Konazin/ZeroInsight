import { useState } from "react";
import { Upload } from "lucide-react";
import { api } from "../../lib/api";
import { FileDropzone } from "../common/FileDropzone";

export function BrandImportPanel({ onImported }: { onImported: () => void }) {
  const [path, setPath] = useState("");
  const [brandName, setBrandName] = useState("");
  const [status, setStatus] = useState<{ text: string; kind: "info" | "success" | "error" } | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    if (!path.trim()) {
      setStatus({ text: "Informe o caminho do arquivo.", kind: "error" });
      return;
    }
    setLoading(true);
    setStatus({ text: "Importando...", kind: "info" });
    try {
      await api.importBrand(path.trim(), brandName.trim() || undefined, false);
      setStatus({ text: "Marca importada com sucesso.", kind: "success" });
      setPath("");
      setBrandName("");
      onImported();
    } catch (error) {
      setStatus({ text: error instanceof Error ? error.message : "Falha ao importar.", kind: "error" });
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel">
      <h2>Importar marca</h2>
      <FileDropzone value={path} onChange={setPath} />
      <label className="field">
        <span>Nome da marca (opcional)</span>
        <input value={brandName} onChange={(event) => setBrandName(event.target.value)} placeholder="Ex: Escritório Exemplo" />
      </label>
      <button onClick={submit} disabled={loading}>
        <Upload size={16} /> {loading ? "Importando..." : "Importar"}
      </button>
      {status && <p className={`feedback ${status.kind}`} style={{ marginTop: 8, marginBottom: 0 }}>{status.text}</p>}
    </section>
  );
}
