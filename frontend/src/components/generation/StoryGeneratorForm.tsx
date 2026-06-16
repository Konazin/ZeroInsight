import { useState } from "react";
import { WandSparkles } from "lucide-react";
import { api } from "../../lib/api";
import { ImagePromptPreview } from "./ImagePromptPreview";
import { StoryPreviewGrid } from "./StoryPreviewGrid";

export function StoryGeneratorForm() {
  const [topic, setTopic] = useState("RPV Federal");
  const [prompt, setPrompt] = useState("");
  const [result, setResult] = useState("");

  async function preview() {
    const response = await api.imagePreview({ topic, visual_idea: "ambiente institucional limpo" }) as { prompt?: string };
    setPrompt(response.prompt ?? "");
  }

  async function generate() {
    const response = await api.generateStory({ topic, slides: 3 }) as { manifest?: { outputs?: { manifest?: string } } };
    setResult(response.manifest?.outputs?.manifest ?? "Geracao finalizada.");
  }

  return (
    <section className="panel">
      <h2>Gerar Stories</h2>
      <div className="stepper"><span>1 Marca</span><span>2 Briefing</span><span>3 Prompt</span><span>4 Exportar</span></div>
      <input value={topic} onChange={(event) => setTopic(event.target.value)} placeholder="Tema" />
      <div className="form-row">
        <button onClick={preview}><WandSparkles size={16} /> Prever prompt</button>
        <button onClick={generate}><WandSparkles size={16} /> Gerar pacote</button>
      </div>
      <div className="split">
        <ImagePromptPreview value={prompt} />
        <StoryPreviewGrid />
      </div>
      <small>{result}</small>
    </section>
  );
}
