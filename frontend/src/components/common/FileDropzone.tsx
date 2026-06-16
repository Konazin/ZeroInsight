export function FileDropzone({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  return (
    <label className="dropzone">
      <span>Caminho local do PDF/DOCX</span>
      <input value={value} onChange={(event) => onChange(event.target.value)} placeholder="C:\\manual\\marca.pdf" />
    </label>
  );
}
