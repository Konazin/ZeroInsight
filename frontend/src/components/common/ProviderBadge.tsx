export function ProviderBadge({ label, value }: { label: string; value: string }) {
  return <span className="provider-badge">{label}: {value}</span>;
}
