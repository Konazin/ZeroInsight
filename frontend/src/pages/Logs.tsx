import { useEffect, useState } from "react";
import { LogPanel } from "../components/common/LogPanel";
import { api } from "../lib/api";

export function Logs() {
  const [lines, setLines] = useState<string[]>([]);
  useEffect(() => { void api.logs().then(setLines); }, []);
  return <section className="panel"><h2>Logs</h2><LogPanel lines={lines} /></section>;
}
