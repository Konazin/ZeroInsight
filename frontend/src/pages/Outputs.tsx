import { useEffect, useState } from "react";
import { EmptyState } from "../components/common/EmptyState";
import { api } from "../lib/api";
import { formatDate } from "../lib/utils";
import type { OutputItem } from "../types";

export function Outputs() {
  const [outputs, setOutputs] = useState<OutputItem[]>([]);
  useEffect(() => { void api.outputs().then(setOutputs); }, []);
  return <section className="panel"><h2>Saidas</h2>{outputs.length === 0 ? <EmptyState title="Nenhuma saida encontrada." /> : outputs.map((item) => <div className="list-row" key={item.path}><strong>{item.name}</strong><span>{item.type} - {formatDate(item.modified_at)}</span></div>)}</section>;
}
