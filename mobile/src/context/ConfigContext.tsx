import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { loadConfig, saveConfig, type AppConfig } from "../lib/secureStore";

type ConfigContextValue = {
  config: AppConfig;
  loading: boolean;
  hasKey: boolean;
  update: (next: AppConfig) => Promise<void>;
  reload: () => Promise<void>;
};

const ConfigContext = createContext<ConfigContextValue | null>(null);

export function ConfigProvider({ children }: { children: ReactNode }) {
  const [config, setConfig] = useState<AppConfig>({ apiKey: "", textModel: "", imageModel: "" });
  const [loading, setLoading] = useState(true);

  async function reload() {
    setLoading(true);
    setConfig(await loadConfig());
    setLoading(false);
  }

  useEffect(() => {
    void reload();
  }, []);

  async function update(next: AppConfig) {
    await saveConfig(next);
    setConfig(next);
  }

  const value = useMemo<ConfigContextValue>(
    () => ({ config, loading, hasKey: Boolean(config.apiKey), update, reload }),
    [config, loading],
  );

  return <ConfigContext.Provider value={value}>{children}</ConfigContext.Provider>;
}

export function useConfig(): ConfigContextValue {
  const ctx = useContext(ConfigContext);
  if (!ctx) throw new Error("useConfig deve ser usado dentro de ConfigProvider");
  return ctx;
}
