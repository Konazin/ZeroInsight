import { ProviderSettings } from "../components/providers/ProviderSettings";
import { ProviderTestPanel } from "../components/providers/ProviderTestPanel";
import type { ProviderState } from "../types";

export function Providers({ providers }: { providers: ProviderState | null; onRefresh: () => void }) {
  return <div className="grid two"><ProviderSettings providers={providers} /><ProviderTestPanel /></div>;
}
