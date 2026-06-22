import { useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { LogPanel } from "../components/common/LogPanel";
import { api } from "../lib/api";

export function Logs() {
  const [lines, setLines] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = async () => {
    setLoading(true);
    try {
      const data = await api.logs();
      setLines(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void refresh(); }, []);

  return (
    <section className="panel">
      <div className="section-header">
        <h2>Logs</h2>
        <button className="btn-ghost btn-sm" onClick={refresh} disabled={loading}>
          <RefreshCw size={14} style={{ animation: loading ? "spin 1s linear infinite" : "none" }} />
          {loading ? "..." : "Atualizar"}
        </button>
      </div>
      <LogPanel lines={lines} />
    </section>
  );
}
