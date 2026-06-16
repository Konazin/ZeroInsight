import { useState } from "react";
import { FlaskConical } from "lucide-react";
import { api } from "../../lib/api";

export function ProviderTestPanel() {
  const [kind, setKind] = useState("text");
  const [name, setName] = useState("mock");
  const [result, setResult] = useState("");

  async function test() {
    const response = await api.testProvider(kind, name);
    setResult(response.message);
  }

  return (
    <section className="panel">
      <h2>Teste rapido</h2>
      <div className="form-row">
        <select value={kind} onChange={(event) => setKind(event.target.value)}><option>text</option><option>image</option><option>vision</option></select>
        <input value={name} onChange={(event) => setName(event.target.value)} />
        <button onClick={test}><FlaskConical size={16} /> Testar</button>
      </div>
      <small>{result}</small>
    </section>
  );
}
