import { BarChart3, Bot, FileText, FolderOpen, Home, Image, ScrollText, Settings, Sparkles, Tags } from "lucide-react";
import type { ComponentType } from "react";
import type { Page } from "../../App";
import { cn } from "../../lib/utils";
import { APP_VERSION } from "../../lib/version";

type NavGroup = {
  label?: string;
  items: Array<{ id: Page; label: string; icon: ComponentType<{ size?: number }> }>;
};

const NAV_GROUPS: NavGroup[] = [
  {
    items: [
      { id: "dashboard", label: "Início", icon: Home },
    ],
  },
  {
    label: "Criar",
    items: [
      { id: "stories", label: "Stories", icon: Image },
      { id: "posts",   label: "Posts",   icon: FileText },
    ],
  },
  {
    label: "Biblioteca",
    items: [
      { id: "brands",  label: "Marcas", icon: Tags },
      { id: "outputs", label: "Saídas", icon: FolderOpen },
    ],
  },
  {
    label: "Sistema",
    items: [
      { id: "providers", label: "IA / Providers",  icon: Bot },
      { id: "settings",  label: "Configurações",   icon: Settings },
      { id: "logs",      label: "Logs",             icon: ScrollText },
    ],
  },
];

export function Sidebar({ page, setPage }: { page: Page; setPage: (page: Page) => void }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="brand-icon"><BarChart3 size={16} color="#fff" /></span>
        ZeroInsight
      </div>

      {/* Ação principal */}
      <div className="sidebar-cta">
        <button className="sidebar-cta-btn" onClick={() => setPage("stories")}>
          <Sparkles size={14} /> Criar Story
        </button>
      </div>

      <nav>
        {NAV_GROUPS.map((group, gi) => (
          <div key={gi}>
            {group.label && <div className="nav-section">{group.label}</div>}
            {group.items.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  className={cn("nav-item", page === item.id && "active")}
                  onClick={() => setPage(item.id)}
                  title={item.label}
                >
                  <Icon size={15} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="sidebar-spacer" />
      <div className="sidebar-footer">ZeroInsight · v{APP_VERSION}</div>
    </aside>
  );
}
