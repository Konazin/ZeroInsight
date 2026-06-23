import type { BrandColor, BrandItem, BrandProfile, Health, OutputItem, PromptTemplate, ProviderState, Settings } from "../types";

const API_BASE = import.meta.env.VITE_ZEROINSIGHT_API ?? "http://127.0.0.1:8765/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { ...(init?.headers ?? {}), "Content-Type": "application/json" },
  });
  if (!response.ok) {
    const text = await response.text();
    let detail = text;
    try {
      const json = JSON.parse(text) as { detail?: string };
      if (json.detail) detail = String(json.detail);
    } catch {
      // text is not JSON, use as-is
    }
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
  getBrand: (id: string) => request<BrandProfile>(`/brands/${id}`),
  updateBrand: (id: string, data: Partial<Omit<BrandProfile, "status" | "created_at" | "source_document_path" | "assets">>) =>
    request<{ ok: boolean }>(`/brands/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  uploadBrandLogo: (id: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return fetch(`${API_BASE}/brands/${id}/logo`, { method: "POST", body: form }).then(async (r) => {
      if (!r.ok) throw new Error(await r.text());
      return r.json() as Promise<{ ok: boolean; logo_path: string }>;
    });
  },
  brandLogoUrl: (id: string, bust?: number) =>
    `${API_BASE}/brands/${id}/logo${bust ? `?t=${bust}` : ""}`,
  importBrand: (path: string, brand_name?: string, use_external_ai = false) =>
    request("/brands/import", { method: "POST", body: JSON.stringify({ path, brand_name, use_external_ai }) }),
  outputs: () => request<OutputItem[]>("/outputs"),
  logs: () => request<string[]>("/logs"),
  braveStatus: () => request<{ ok: boolean; message: string }>("/brave/status"),
  braveStart: () => request<{ ok: boolean; message: string }>("/brave/start", { method: "POST" }),
  imagePreview: (payload: object) => request("/generate/image-preview", { method: "POST", body: JSON.stringify(payload) }),
  generateStory: (payload: object) => request("/generate/story", { method: "POST", body: JSON.stringify(payload) }),
  generatePost: (payload: object) => request("/generate/post", { method: "POST", body: JSON.stringify(payload) }),
  prompts: () => request<PromptTemplate[]>("/prompts"),
  savePrompt: (data: { name: string; prompt: string; description?: string; brand_id?: string | null; tags?: string[] }) =>
    request<PromptTemplate>("/prompts", { method: "POST", body: JSON.stringify(data) }),
  deletePrompt: (id: string) =>
    fetch(`${API_BASE}/prompts/${id}`, { method: "DELETE" }),
  fileUrl: (path: string) => `${API_BASE}/outputs/file?path=${encodeURIComponent(path)}`,
  openFolder: (path: string) =>
    fetch(`${API_BASE}/outputs/open-folder?path=${encodeURIComponent(path)}`, { method: "POST" }),
};
