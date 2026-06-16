export function ImagePromptPreview({ value }: { value: string }) {
  return <textarea className="prompt-preview" value={value} readOnly />;
}
