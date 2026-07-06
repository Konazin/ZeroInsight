/**
 * Cliente OpenAI standalone (chamado direto do dispositivo).
 *
 * Usa fetch — sem SDK — para manter o bundle leve. A chave nunca é logada.
 * Erros de rede/HTTP são normalizados em mensagens amigáveis.
 */

const BASE_URL = "https://api.openai.com/v1";

export class OpenAIError extends Error {}

export type SlideScript = {
  order: number;
  hook: string;
  body: string;
  cta: string;
};

export type StoryBrief = {
  topic: string;
  objective: string;
  audience: string;
  tone: string;
  cta: string;
  slides: number;
};

async function chat(apiKey: string, model: string, system: string, user: string): Promise<string> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model,
        messages: [
          { role: "system", content: system },
          { role: "user", content: user },
        ],
        temperature: 0.8,
      }),
    });
  } catch {
    throw new OpenAIError("Falha de rede ao contatar a OpenAI. Verifique sua conexão.");
  }

  if (!res.ok) {
    throw new OpenAIError(await describeHttpError(res));
  }
  const data = (await res.json()) as { choices?: Array<{ message?: { content?: string } }> };
  const content = data.choices?.[0]?.message?.content?.trim();
  if (!content) throw new OpenAIError("A OpenAI retornou uma resposta vazia.");
  return content;
}

/** Gera o roteiro de slides como JSON estruturado. */
export async function generateScript(
  apiKey: string,
  textModel: string,
  brief: StoryBrief,
): Promise<SlideScript[]> {
  const system =
    "Você é um redator de Instagram Stories para marketing jurídico. " +
    "Responda SOMENTE com JSON válido, sem markdown, no formato " +
    '{"slides":[{"order":1,"hook":"...","body":"...","cta":"..."}]}. ' +
    "Evite promessas absolutas (garantido, 100%, sem risco).";
  const user =
    `Tema: ${brief.topic}\nObjetivo: ${brief.objective}\nPúblico: ${brief.audience}\n` +
    `Tom: ${brief.tone}\nCTA: ${brief.cta}\nQuantidade de slides: ${brief.slides}\n` +
    `Gere ${brief.slides} slides curtos e impactantes.`;

  const raw = await chat(apiKey, textModel, system, user);
  const parsed = safeParseSlides(raw);
  if (!parsed.length) throw new OpenAIError("Não foi possível interpretar o roteiro gerado.");
  return parsed.slice(0, brief.slides);
}

/** Gera uma imagem 9:16 e retorna a string base64 (sem prefixo data URI). */
export async function generateImage(
  apiKey: string,
  imageModel: string,
  prompt: string,
): Promise<string> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}/images/generations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify({
        model: imageModel,
        prompt,
        size: "1024x1536",
        n: 1,
      }),
    });
  } catch {
    throw new OpenAIError("Falha de rede ao gerar a imagem.");
  }
  if (!res.ok) throw new OpenAIError(await describeHttpError(res));

  const data = (await res.json()) as { data?: Array<{ b64_json?: string }> };
  const b64 = data.data?.[0]?.b64_json;
  if (!b64) throw new OpenAIError("A OpenAI não retornou imagem.");
  return b64;
}

/** Valida a chave com uma chamada leve a /models. */
export async function validateKey(apiKey: string): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/models`, {
      headers: { Authorization: `Bearer ${apiKey}` },
    });
    return res.ok;
  } catch {
    return false;
  }
}

// ── Helpers ─────────────────────────────────────────────────────────────────

async function describeHttpError(res: Response): Promise<string> {
  if (res.status === 401) return "Chave de API inválida ou expirada. Confira em Configurações.";
  if (res.status === 429) return "Limite de uso atingido (429). Tente novamente em instantes.";
  if (res.status === 400) return "Requisição rejeitada pela OpenAI (400). Ajuste o briefing.";
  let detail = "";
  try {
    const body = (await res.json()) as { error?: { message?: string } };
    detail = body.error?.message ? ` — ${body.error.message}` : "";
  } catch {
    /* ignore */
  }
  return `Erro da OpenAI (${res.status})${detail}`;
}

function safeParseSlides(raw: string): SlideScript[] {
  // Remove cercas de markdown, se houver.
  const cleaned = raw.replace(/```json/gi, "").replace(/```/g, "").trim();
  try {
    const obj = JSON.parse(cleaned) as { slides?: unknown };
    const slides = Array.isArray(obj.slides) ? obj.slides : [];
    return slides.map((s, i) => {
      const slide = s as Partial<SlideScript>;
      return {
        order: slide.order ?? i + 1,
        hook: String(slide.hook ?? ""),
        body: String(slide.body ?? ""),
        cta: String(slide.cta ?? ""),
      };
    });
  } catch {
    return [];
  }
}
