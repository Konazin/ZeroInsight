import { useEffect, useState } from "react";
import { RefreshCw, FolderOpen } from "lucide-react";
import { api } from "../lib/api";
import { formatDate } from "../lib/utils";
import type { OutputItem } from "../types";

function formatSize(bytes?: number): string {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function Outputs() {
  const [outputs, setOutputs] = useState<OutputItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<"all" | "story" | "post">("all");

  const refresh = async () => {
    setLoading(true);
    try {
      const data = await api.outputs();
      setOutputs(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { void refresh(); }, []);

  const visible = filter === "all" ? outputs : outputs.filter((o) => o.type === filter);
  const storyCount = outputs.filter((o) => o.type === "story").length;
  const postCount = outputs.filter((o) => o.type === "post").length;

  return (
    <section className="panel">
      <div className="section-header">
        <h2>Saídas</h2>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <select
            value={filter}
            onChange={(e) => setFilter(e.target.value as "all" | "story" | "post")}
            style={{ width: "auto", padding: "6px 10px", fontSize: 13 }}
          >
            <option value="all">Todos ({outputs.length})</option>
            <option value="story">Stories ({storyCount})</option>
            <option value="post">Posts ({postCount})</option>
          </select>
          <button className="btn-ghost btn-sm" onClick={refresh} disabled={loading} title="Atualizar">
            <RefreshCw size={14} style={{ animation: loading ? "spin 1s linear infinite" : "none" }} />
            {loading ? "..." : "Atualizar"}
          </button>
        </div>
      </div>

      {loading && outputs.length === 0 ? (
        <div className="loading-state">Carregando saídas...</div>
      ) : visible.length === 0 ? (
        <div className="empty-state" style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
          <FolderOpen size={24} style={{ opacity: 0.4 }} />
          <span>{filter === "all" ? "Nenhuma saída encontrada." : `Nenhum ${filter} encontrado.`}</span>
        </div>
      ) : (
        <div className="list">
          {visible.map((item) => (
            <div className="list-row" key={item.path}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, minWidth: 0 }}>
                <span className={`tag ${item.type}`}>{item.type}</span>
                <strong style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", color: "var(--text-primary)" }}>{item.name}</strong>
              </div>
              <div style={{ display: "flex", gap: 12, alignItems: "center", flexShrink: 0 }}>
                {item.size ? <span style={{ fontSize: 12, color: "var(--text-subtle)" }}>{formatSize(item.size)}</span> : null}
                <span style={{ fontSize: 13 }}>{formatDate(item.modified_at)}</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
