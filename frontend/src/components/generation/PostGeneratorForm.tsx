import { useEffect, useState } from "react";
import { FileText } from "lucide-react";
import { api } from "../../lib/api";
import type { BrandItem } from "../../types";

type Status = { text: string; kind: "success" | "error" | "info" } | null;

export function PostGeneratorForm() {
  const [brands, setBrands] = useState<BrandItem[]>([]);
  const [brandId, setBrandId] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<Status>(null);

  useEffect(() => {
    void api.brands().then((b) => {
      setBrands(b);
      if (b.length > 0) setBrandId(b[0].id);
    }).catch(() => {});
  }, []);

  async function generate() {
    setLoading(true);
    setStatus({ text: "Executando pipeline de geração...", kind: "info" });
    setResult("");
    try {
      const payload = brandId ? { brand: brandId } : {};
      const response = await api.generatePost(payload);
      setResult(JSON.stringify(response, null, 2));
      setStatus({ text: "Post gerado com sucesso.", kind: "success" });
    } catch (error) {
      setStatus({ text: error instanceof Error ? error.message : "Falha ao gerar post.", kind: "error" });
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="panel">
      <div className="section-header">
        <h2>Gerar Post</h2>
      </div>
      <p style={{ margin: "0 0 18px", color: "var(--text-muted)", fontSize: 14, lineHeight: 1.6 }}>
        Executa o pipeline completo de geração de post jurídico com base nas marcas e provedores configurados.
      </p>

      {brands.length > 0 && (
        <label className="field">
          <span>Marca</span>
          <select value={brandId} onChange={(e) => setBrandId(e.target.value)}>
            <option value="">Sem marca específica</option>
            {brands.map((b) => (
              <option key={b.id} value={b.id}>{b.name}</option>
            ))}
          </select>
        </label>
      )}

      <button onClick={generate} disabled={loading}>
        <FileText size={16} /> {loading ? "Gerando..." : "Gerar post via pipeline"}
      </button>
      {status && <p className={`feedback ${status.kind}`}>{status.text}</p>}

      {result && (
        <div style={{ marginTop: 16 }}>
          <p style={{ margin: "0 0 6px", fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)" }}>Resultado</p>
          <pre className="small-pre">{result}</pre>
        </div>
      )}
    </section>
  );
}
