import { useEffect, useState } from "react";
import { BrandImportPanel } from "../components/brand/BrandImportPanel";
import { BrandPreview } from "../components/brand/BrandPreview";
import { BrandProfileEditor } from "../components/brand/BrandProfileEditor";
import { api } from "../lib/api";
import type { BrandItem } from "../types";

export function Brands() {
  const [brands, setBrands] = useState<BrandItem[]>([]);
  const refresh = () => void api.brands().then(setBrands);
  useEffect(refresh, []);
  return <div className="grid two"><BrandImportPanel onImported={refresh} /><BrandPreview brands={brands} /><BrandProfileEditor /></div>;
}
