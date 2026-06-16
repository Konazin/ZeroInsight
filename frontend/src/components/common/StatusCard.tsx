export function StatusCard({ title, value, tone = "neutral" }: { title: string; value: string; tone?: "neutral" | "success" | "warning" | "danger" }) {
  return (
    <div className={`status-card ${tone}`}>
      <span>{title}</span>
      <strong>{value}</strong>
    </div>
  );
}
