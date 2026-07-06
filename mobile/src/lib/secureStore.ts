/**
 * Armazenamento seguro da chave de API e preferências.
 *
 * A chave OpenAI é guardada com expo-secure-store (Keychain no iOS,
 * Keystore no Android) — NUNCA em AsyncStorage/texto puro. Config não
 * sensível (modelos) fica no mesmo cofre por simplicidade.
 */
import * as SecureStore from "expo-secure-store";

const KEYS = {
  openaiApiKey: "zi_openai_api_key",
  textModel: "zi_text_model",
  imageModel: "zi_image_model",
} as const;

export const DEFAULT_TEXT_MODEL = "gpt-5.4-mini";
export const DEFAULT_IMAGE_MODEL = "gpt-image-2";

export type AppConfig = {
  apiKey: string;
  textModel: string;
  imageModel: string;
};

async function get(key: string): Promise<string | null> {
  try {
    return await SecureStore.getItemAsync(key);
  } catch {
    return null;
  }
}

async function set(key: string, value: string): Promise<void> {
  if (value) {
    await SecureStore.setItemAsync(key, value);
  } else {
    await SecureStore.deleteItemAsync(key);
  }
}

export async function loadConfig(): Promise<AppConfig> {
  const [apiKey, textModel, imageModel] = await Promise.all([
    get(KEYS.openaiApiKey),
    get(KEYS.textModel),
    get(KEYS.imageModel),
  ]);
  return {
    apiKey: apiKey ?? "",
    textModel: textModel || DEFAULT_TEXT_MODEL,
    imageModel: imageModel || DEFAULT_IMAGE_MODEL,
  };
}

export async function saveConfig(config: AppConfig): Promise<void> {
  await Promise.all([
    set(KEYS.openaiApiKey, config.apiKey.trim()),
    set(KEYS.textModel, config.textModel.trim() || DEFAULT_TEXT_MODEL),
    set(KEYS.imageModel, config.imageModel.trim() || DEFAULT_IMAGE_MODEL),
  ]);
}

export async function clearApiKey(): Promise<void> {
  await SecureStore.deleteItemAsync(KEYS.openaiApiKey);
}

/** Máscara para exibir a chave sem revelá-la (sk-abcd...wxyz). */
export function maskKey(key: string): string {
  if (!key) return "(não configurada)";
  if (key.length <= 8) return "****";
  return `${key.slice(0, 5)}…${key.slice(-4)}`;
}
