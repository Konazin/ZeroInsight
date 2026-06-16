import type { BrandItem } from "../../types";

export function BrandPreview({ brands }: { brands: BrandItem[] }) {
  return (
    <section className="panel">
      <h2>Marcas salvas</h2>
      <div className="list">
        {brands.map((brand) => <div className="list-row" key={brand.id}><strong>{brand.name}</strong><span>{brand.path}</span></div>)}
      </div>
    </section>
  );
}
