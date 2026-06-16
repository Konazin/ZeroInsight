import { useState } from "react";
import { FileText } from "lucide-react";
import { api } from "../../lib/api";

export function PostGeneratorForm() {
  const [result, setResult] = useState("");
  async function generate() {
    const response = await api.generatePost({});
    setResult(JSON.stringify(response, null, 2));
  }
  return <section className="panel"><h2>Gerar Post</h2><button onClick={generate}><FileText size={16} /> Gerar post via pipeline</button><pre className="small-pre">{result}</pre></section>;
}
