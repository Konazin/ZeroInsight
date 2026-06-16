import type { BrandItem, Health, OutputItem, ProviderState, Settings } from "../types";

const API_BASE = import.meta.env.VITE_ZEROINSIGHT_API ?? "http://127.0.0.1:8765/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<Health>("/health"),
  settings: () => request<Settings>("/settings"),
  saveSettings: (values: Settings) => request<Settings>("/settings", { method: "POST", body: JSON.stringify(values) }),
  providers: () => request<ProviderState>("/providers"),
  testProvider: (kind: string, name: string) => request<{ ok: boolean; message: string }>("/providers/test", { method: "POST", body: JSON.stringify({ kind, name }) }),
  brands: () => request<BrandItem[]>("/brands"),
  importBrand: (path: string, brand_name?: string, use_external_ai = false) =>
    request("/brands/import", { method: "POST", body: JSON.stringify({ path, brand_name, use_external_ai }) }),
  outputs: () => request<OutputItem[]>("/outputs"),
  logs: () => request<string[]>("/logs"),
  braveStatus: () => request<{ ok: boolean; message: string }>("/brave/status"),
  braveStart: () => request<{ ok: boolean; message: string }>("/brave/start", { method: "POST" }),
  imagePreview: (payload: object) => request("/generate/image-preview", { method: "POST", body: JSON.stringify(payload) }),
  generateStory: (payload: object) => request("/generate/story", { method: "POST", body: JSON.stringify(payload) }),
  generatePost: (payload: object) => request("/generate/post", { method: "POST", body: JSON.stringify(payload) }),
};
