import { Tags } from "lucide-react";
import type { BrandItem } from "../../types";

export function BrandPreview({ brands, selected, onSelect }: { brands: BrandItem[]; selected: BrandItem | null; onSelect: (brand: BrandItem | null) => void }) {
  return (
    <section className="panel">
      <div className="section-header">
        <h2>Marcas salvas</h2>
        <span className="tag">{brands.length} marca{brands.length !== 1 ? "s" : ""}</span>
      </div>
      {brands.length === 0 ? (
        <div className="empty-state" style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
          <Tags size={24} style={{ opacity: 0.4 }} />
          <span>Nenhuma marca importada.</span>
        </div>
      ) : (
        <div className="list">
          {brands.map((brand) => (
            <div
              key={brand.id}
              className={`list-row clickable${selected?.id === brand.id ? " selected" : ""}`}
              onClick={() => onSelect(selected?.id === brand.id ? null : brand)}
            >
              <strong>{brand.name}</strong>
              <span title={brand.path}>{brand.path.split(/[\\/]/).pop()}</span>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
