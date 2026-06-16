export type Health = { status: string; service: string; time: string };
export type ProviderState = {
  available: Record<string, string[]>;
  active: { text: string; image: string; vision: string };
  openai: { configured: boolean; text_model: string; reasoning_model: string; image_model: string; image_size: string };
};
export type BrandItem = { id: string; name: string; path: string };
export type OutputItem = { type: string; name: string; path: string; modified_at: number };
export type Settings = Record<string, string | number | boolean | object | null>;
