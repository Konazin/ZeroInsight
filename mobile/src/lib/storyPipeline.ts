/**
 * Pipeline de geração de Stories no dispositivo.
 *
 * Orquestra: roteiro (texto) → prompt visual por slide → imagem → salva no
 * armazenamento local do app. Cada campanha vira uma pasta em
 * `documentDirectory/stories/<timestamp>_<slug>/`.
 */
import * as FileSystem from "expo-file-system";
import {
  generateImage,
  generateScript,
  type SlideScript,
  type StoryBrief,
} from "./openai";
import type { AppConfig } from "./secureStore";

export type GeneratedSlide = SlideScript & { imageUri: string };

export type StoryResult = {
  directory: string;
  campaign: string;
  createdAt: number;
  slides: GeneratedSlide[];
};

export type ProgressUpdate = { step: string; current: number; total: number };

const STORIES_DIR = `${FileSystem.documentDirectory}stories/`;

function slugify(value: string): string {
  return (
    value
      .toLowerCase()
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "")
      .slice(0, 40) || "story"
  );
}

function buildImagePrompt(brief: StoryBrief, slide: SlideScript): string {
  return (
    `Instagram Story vertical 9:16 para marketing jurídico institucional. ` +
    `Tema: ${brief.topic}. Tom: ${brief.tone}. ` +
    `Componha um design limpo e premium com o título "${slide.hook}", ` +
    `um corpo de texto curto "${slide.body}" e a chamada "${slide.cta}". ` +
    `Fundo institucional elegante, boa legibilidade, área de segurança nas bordas. ` +
    `Sem logos de terceiros, sem watermark.`
  );
}

async function ensureDir(path: string): Promise<void> {
  const info = await FileSystem.getInfoAsync(path);
  if (!info.exists) {
    await FileSystem.makeDirectoryAsync(path, { intermediates: true });
  }
}

export async function runStoryPipeline(
  config: AppConfig,
  brief: StoryBrief,
  onProgress?: (u: ProgressUpdate) => void,
): Promise<StoryResult> {
  const total = brief.slides + 1;
  onProgress?.({ step: "Gerando roteiro com IA…", current: 1, total });
  const script = await generateScript(config.apiKey, config.textModel, brief);

  const campaign = `${Date.now()}_${slugify(brief.topic)}`;
  const directory = `${STORIES_DIR}${campaign}/`;
  const stagingDirectory = `${STORIES_DIR}.${campaign}.in_progress/`;
  await ensureDir(stagingDirectory);

  const slides: GeneratedSlide[] = [];
  try {
    for (let i = 0; i < script.length; i++) {
      const slide = script[i];
      onProgress?.({ step: `Gerando imagem ${i + 1}/${script.length}…`, current: i + 2, total });
      const b64 = await generateImage(config.apiKey, config.imageModel, buildImagePrompt(brief, slide));
      const imageUri = `${stagingDirectory}story_${String(i + 1).padStart(2, "0")}.png`;
      await FileSystem.writeAsStringAsync(imageUri, b64, {
        encoding: FileSystem.EncodingType.Base64,
      });
      slides.push({ ...slide, imageUri });
    }

    const createdAt = Date.now();
    await FileSystem.writeAsStringAsync(
      `${stagingDirectory}manifest.json`,
      JSON.stringify({ brief, slides: script, createdAt, status: "COMPLETE" }, null, 2),
    );
    await FileSystem.moveAsync({ from: stagingDirectory, to: directory });
    return {
      directory,
      campaign,
      createdAt,
      slides: slides.map((slide) => ({
        ...slide,
        imageUri: slide.imageUri.replace(stagingDirectory, directory),
      })),
    };
  } catch (error) {
    await FileSystem.deleteAsync(stagingDirectory, { idempotent: true }).catch(() => {});
    throw error;
  }
}

/** Lista campanhas geradas previamente (mais recentes primeiro). */
export async function listCampaigns(): Promise<StoryResult[]> {
  await ensureDir(STORIES_DIR);
  const entries = await FileSystem.readDirectoryAsync(STORIES_DIR);
  const results: StoryResult[] = [];

  for (const name of entries) {
    if (name.startsWith(".") || name.endsWith(".in_progress")) continue;
    const dir = `${STORIES_DIR}${name}/`;
    try {
      const files = await FileSystem.readDirectoryAsync(dir);
      const images = files
        .filter((f) => f.endsWith(".png"))
        .sort()
        .map((f, i) => ({
          order: i + 1,
          hook: "",
          body: "",
          cta: "",
          imageUri: `${dir}${f}`,
        }));
      if (!images.length) continue;
      const tsPart = Number(name.split("_")[0]);
      results.push({
        directory: dir,
        campaign: name,
        createdAt: Number.isFinite(tsPart) ? tsPart : 0,
        slides: images,
      });
    } catch {
      /* ignora pastas ilegíveis */
    }
  }
  return results.sort((a, b) => b.createdAt - a.createdAt);
}

export async function deleteCampaign(directory: string): Promise<void> {
  await FileSystem.deleteAsync(directory, { idempotent: true });
}
