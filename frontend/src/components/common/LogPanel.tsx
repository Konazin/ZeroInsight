import { useEffect, useRef } from "react";

export function LogPanel({ lines }: { lines: string[] }) {
  const ref = useRef<HTMLPreElement>(null);

  useEffect(() => {
    if (ref.current) {
      ref.current.scrollTop = ref.current.scrollHeight;
    }
  }, [lines]);

  return (
    <pre className="log-panel" ref={ref}>
      {lines.length ? lines.join("\n") : "Sem logs disponíveis."}
    </pre>
  );
}
