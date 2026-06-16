export function LogPanel({ lines }: { lines: string[] }) {
  return <pre className="log-panel">{lines.length ? lines.join("\n") : "Sem logs disponiveis."}</pre>;
}
