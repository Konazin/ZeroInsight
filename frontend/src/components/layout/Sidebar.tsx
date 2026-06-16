import { BarChart3, Bot, FileText, FolderOpen, Home, Image, Logs, Settings, Tags } from "lucide-react";
import type { ComponentType } from "react";
import type { Page } from "../../App";
import { cn } from "../../lib/utils";

const items: Array<{ id: Page; label: string; icon: ComponentType<{ size?: number }> }> = [
  { id: "dashboard", label: "Dashboard", icon: Home },
  { id: "brands", label: "Marcas", icon: Tags },
  { id: "providers", label: "IA / Providers", icon: Bot },
  { id: "stories", label: "Gerar Stories", icon: Image },
  { id: "posts", label: "Gerar Posts", icon: FileText },
  { id: "outputs", label: "Saidas", icon: FolderOpen },
  { id: "settings", label: "Configuracoes", icon: Settings },
  { id: "logs", label: "Logs", icon: Logs },
];

export function Sidebar({ page, setPage }: { page: Page; setPage: (page: Page) => void }) {
  return (
    <aside className="sidebar">
      <div className="brand"><BarChart3 size={22} /> ZeroInsight</div>
      <nav>
        {items.map((item) => {
          const Icon = item.icon;
          return (
            <button key={item.id} className={cn("nav-item", page === item.id && "active")} onClick={() => setPage(item.id)} title={item.label}>
              <Icon size={18} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
