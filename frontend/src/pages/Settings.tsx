import { SettingsPanel } from "../components/settings/SettingsPanel";

export function SettingsPage({ onSaved }: { onSaved: () => void }) {
  return <SettingsPanel onSaved={onSaved} />;
}
