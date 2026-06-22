import { useEffect, useState } from "react";
import { BrandImportPanel } from "../components/brand/BrandImportPanel";
import { BrandPreview } from "../components/brand/BrandPreview";
import { BrandProfileEditor } from "../components/brand/BrandProfileEditor";
import { api } from "../lib/api";
import type { BrandItem } from "../types";

export function Brands() {
  const [brands, setBrands] = useState<BrandItem[]>([]);
  const [selected, setSelected] = useState<BrandItem | null>(null);

  const refresh = () =>
    void api.brands().then((list) => {
      setBrands(list);
      if (selected) {
        const updated = list.find((b) => b.id === selected.id);
        setSelected(updated ?? null);
      }
    });

  useEffect(refresh, []);

  return (
    <div style={{ display: "grid", gap: 16, gridTemplateColumns: "1fr 1fr" }}>
      <BrandImportPanel onImported={refresh} />
      <BrandPreview brands={brands} selected={selected} onSelect={setSelected} />
      <div style={{ gridColumn: "1 / -1" }}>
        <BrandProfileEditor brand={selected} />
      </div>
    </div>
  );
}
