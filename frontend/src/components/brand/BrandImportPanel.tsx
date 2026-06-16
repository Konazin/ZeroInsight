import { useState } from "react";
import { Upload } from "lucide-react";
import { api } from "../../lib/api";
import { FileDropzone } from "../common/FileDropzone";

export function BrandImportPanel({ onImported }: { onImported: () => void }) {
  const [path, setPath] = useState("");
  const [brandName, setBrandName] = useState("");
  const [status, setStatus] = useState("");

  async function submit() {
    setStatus("Importando...");
    try {
      await api.importBrand(path, brandName || undefined, false);
      setStatus("Marca importada.");
      onImported();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Falha ao importar.");
    }
  }

  return (
    <section className="panel">
      <h2>Importar marca</h2>
      <FileDropzone value={path} onChange={setPath} />
      <input value={brandName} onChange={(event) => setBrandName(event.target.value)} placeholder="Nome da marca" />
      <button onClick={submit}><Upload size={16} /> Importar</button>
      <small>{status}</small>
    </section>
  );
}
