import { useEffect, useRef, useState } from "react";
import type { BrandColor, BrandItem, BrandProfile } from "../../types";
import { api } from "../../lib/api";

// ── helpers ───────────────────────────────────────────────────────────────────

function empty(profile: BrandProfile): EditableProfile {
  return {
    brand_name: profile.brand_name ?? "",
    summary: profile.summary ?? "",
    tone_of_voice: [...(profile.tone_of_voice ?? [])],
    target_audience: [...(profile.target_audience ?? [])],
    cta_style: [...(profile.cta_style ?? [])],
    preferred_terms: [...(profile.preferred_terms ?? [])],
    forbidden_terms: [...(profile.forbidden_terms ?? [])],
    content_rules: [...(profile.content_rules ?? [])],
    compliance_rules: [...(profile.compliance_rules ?? [])],
    visual_style: [...(profile.visual_style ?? [])],
    color_palette: (profile.color_palette ?? []).map((c) => ({ ...c })),
    typography_notes: [...(profile.typography_notes ?? [])],
    layout_rules: [...(profile.layout_rules ?? [])],
    image_style_rules: [...(profile.image_style_rules ?? [])],
    logo_usage_notes: [...(profile.logo_usage_notes ?? [])],
  };
}

type EditableProfile = {
  brand_name: string;
  summary: string;
  tone_of_voice: string[];
  target_audience: string[];
  cta_style: string[];
  preferred_terms: string[];
  forbidden_terms: string[];
  content_rules: string[];
  compliance_rules: string[];
  visual_style: string[];
  color_palette: BrandColor[];
  typography_notes: string[];
  layout_rules: string[];
  image_style_rules: string[];
  logo_usage_notes: string[];
};

// ── main component ────────────────────────────────────────────────────────────

export function BrandProfileEditor({
  brand,
  onUpdated,
}: {
  brand: BrandItem | null;
  onUpdated?: () => void;
}) {
  const [profile, setProfile] = useState<BrandProfile | null>(null);
  const [form, setForm] = useState<EditableProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [logoUrl, setLogoUrl] = useState<string | null>(null);
  const [logoBust, setLogoBust] = useState(0);
  const [logoUploading, setLogoUploading] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const logoInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!brand) { setProfile(null); setForm(null); setLogoUrl(null); return; }
    setLoading(true);
    setError(null);
    setSaved(false);
    void api.getBrand(brand.id)
      .then((p) => {
        setProfile(p);
        setForm(empty(p));
        setLogoUrl(p.assets?.logo_path ? api.brandLogoUrl(brand.id, Date.now()) : null);
      })
      .catch(() => { setProfile(null); setForm(null); })
      .finally(() => setLoading(false));
  }, [brand?.id]);

  if (!brand) {
    return (
      <section className="panel">
        <h2>BrandProfile</h2>
        <p className="muted" style={{ margin: 0 }}>
          Selecione uma marca na lista acima para visualizar e editar seus detalhes.
        </p>
      </section>
    );
  }

  if (loading) {
    return (
      <section className="panel">
        <h2>BrandProfile — {brand.name}</h2>
        <div className="loading-state">Carregando perfil…</div>
      </section>
    );
  }

  if (!form) return null;

  function set<K extends keyof EditableProfile>(field: K, value: EditableProfile[K]) {
    setForm((f) => f ? { ...f, [field]: value } : f);
    setSaved(false);
  }

  async function handleSave() {
    if (!brand || !form) return;
    setSaving(true);
    setError(null);
    try {
      await api.updateBrand(brand.id, form);
      setSaved(true);
      onUpdated?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  async function handleLogoUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !brand) return;
    setLogoUploading(true);
    setError(null);
    try {
      await api.uploadBrandLogo(brand.id, file);
      const bust = Date.now();
      setLogoBust(bust);
      setLogoUrl(api.brandLogoUrl(brand.id, bust));
      onUpdated?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLogoUploading(false);
      if (logoInputRef.current) logoInputRef.current.value = "";
    }
  }

  return (
    <section className="panel">
      {/* Header */}
      <div className="section-header">
        <h2>BrandProfile — {brand.name}</h2>
        <span className="tag" style={{ textTransform: "none", fontSize: 12, letterSpacing: 0 }}>
          {profile?.status ?? "—"}
        </span>
      </div>

      <div className="grid three" style={{ marginBottom: 20 }}>
        <div className="mini-card">ID<strong style={{ fontSize: 12, wordBreak: "break-all" }}>{brand.id}</strong></div>
        <div className="mini-card">Criado<strong style={{ fontSize: 12 }}>{profile?.created_at?.slice(0, 10) ?? "—"}</strong></div>
        <div className="mini-card">Arquivo<strong style={{ fontSize: 12, wordBreak: "break-all" }}>{brand.path.split(/[\\/]/).pop()}</strong></div>
      </div>

      {/* ── Seção: Identidade ── */}
      <ProfileSection title="Identidade da marca">
        <label className="field">
          <span>Nome da marca</span>
          <input value={form.brand_name} onChange={(e) => set("brand_name", e.target.value)} placeholder="Ex: RequisiteRPV" />
        </label>
        <label className="field">
          <span>Resumo / descrição da empresa</span>
          <textarea
            value={form.summary}
            onChange={(e) => set("summary", e.target.value)}
            rows={4}
            placeholder="Descreva a empresa, seus produtos/serviços, diferencial e contexto de mercado…"
            style={{ resize: "vertical" }}
          />
        </label>
      </ProfileSection>

      {/* ── Seção: Tom e Audiência ── */}
      <ProfileSection title="Tom e audiência">
        <div className="field">
          <span>Tom de voz</span>
          <TagEditor value={form.tone_of_voice} onChange={(v) => set("tone_of_voice", v)} placeholder="Ex: institucional, confiável…" />
        </div>
        <div className="field">
          <span>Público-alvo</span>
          <TagEditor value={form.target_audience} onChange={(v) => set("target_audience", v)} placeholder="Ex: servidores públicos…" />
        </div>
        <div className="field">
          <span>Estilo de CTA</span>
          <TagEditor value={form.cta_style} onChange={(v) => set("cta_style", v)} placeholder="Ex: direto, imperativo…" />
        </div>
      </ProfileSection>

      {/* ── Seção: Linguagem ── */}
      <ProfileSection title="Linguagem e conformidade">
        <div className="field">
          <span>Termos preferidos</span>
          <TagEditor value={form.preferred_terms} onChange={(v) => set("preferred_terms", v)} placeholder="Palavras que a marca usa…" />
        </div>
        <div className="field">
          <span>Termos proibidos</span>
          <TagEditor value={form.forbidden_terms} onChange={(v) => set("forbidden_terms", v)} placeholder="Palavras que a marca evita…" />
        </div>
        <div className="field">
          <span>Regras de conteúdo</span>
          <TagEditor value={form.content_rules} onChange={(v) => set("content_rules", v)} placeholder="Ex: não prometer resultados…" />
        </div>
        <div className="field">
          <span>Regras de compliance</span>
          <TagEditor value={form.compliance_rules} onChange={(v) => set("compliance_rules", v)} placeholder="Ex: não usar linguagem sensacionalista…" />
        </div>
      </ProfileSection>

      {/* ── Seção: Visual ── */}
      <ProfileSection title="Identidade visual">
        {/* Logo */}
        <div className="field">
          <span>Logo</span>
          <div className="brand-logo-editor">
            {logoUrl ? (
              <img key={logoBust} src={logoUrl} alt="Logo" className="brand-logo-preview" onError={() => setLogoUrl(null)} />
            ) : (
              <div className="brand-logo-placeholder">
                <span style={{ fontSize: 13, color: "var(--text-subtle)" }}>Sem logo</span>
              </div>
            )}
            <button className="btn-ghost btn-sm" disabled={logoUploading} onClick={() => logoInputRef.current?.click()}>
              {logoUploading ? "Enviando…" : logoUrl ? "Trocar logo" : "Adicionar logo"}
            </button>
            <input ref={logoInputRef} type="file" accept=".png,.jpg,.jpeg,.webp" style={{ display: "none" }} onChange={handleLogoUpload} />
          </div>
        </div>

        {/* Paleta de cores */}
        <div className="field">
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 8 }}>
            <span>Paleta de cores</span>
            <button className="btn-ghost btn-sm" onClick={() => set("color_palette", [...form.color_palette, { name: "Nova cor", hex: "#2563eb", usage: "" }])}>
              + Cor
            </button>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {form.color_palette.map((c, i) => (
              <div key={i} className="brand-color-row">
                <label className="brand-color-swatch-label">
                  <span className="color-swatch" style={{ background: c.hex }} />
                  <input type="color" value={c.hex} className="brand-color-picker"
                    onChange={(e) => {
                      const next = form.color_palette.map((x, j) => j === i ? { ...x, hex: e.target.value } : x);
                      set("color_palette", next);
                    }}
                  />
                </label>
                <input type="text" value={c.hex} maxLength={7} className="brand-hex-input"
                  onChange={(e) => {
                    const hex = e.target.value.startsWith("#") ? e.target.value : `#${e.target.value}`;
                    set("color_palette", form.color_palette.map((x, j) => j === i ? { ...x, hex } : x));
                  }}
                />
                <input type="text" value={c.name} placeholder="Nome" className="brand-color-name"
                  onChange={(e) => set("color_palette", form.color_palette.map((x, j) => j === i ? { ...x, name: e.target.value } : x))}
                />
                <input type="text" value={c.usage ?? ""} placeholder="Uso (ex: primária, fundo…)" className="brand-color-usage"
                  onChange={(e) => set("color_palette", form.color_palette.map((x, j) => j === i ? { ...x, usage: e.target.value } : x))}
                />
                <button className="btn-ghost btn-sm" style={{ padding: "5px 8px", color: "var(--danger)", flexShrink: 0 }}
                  onClick={() => set("color_palette", form.color_palette.filter((_, j) => j !== i))}>×</button>
              </div>
            ))}
            {form.color_palette.length === 0 && (
              <p style={{ margin: 0, fontSize: 13, color: "var(--text-subtle)" }}>Nenhuma cor. Clique em "+ Cor" para adicionar.</p>
            )}
          </div>
        </div>

        <div className="field">
          <span>Estilo visual</span>
          <TagEditor value={form.visual_style} onChange={(v) => set("visual_style", v)} placeholder="Ex: moderno, clean, institucional…" />
        </div>
        <div className="field">
          <span>Notas de tipografia</span>
          <TagEditor value={form.typography_notes} onChange={(v) => set("typography_notes", v)} placeholder="Ex: sans-serif, texto branco…" />
        </div>
        <div className="field">
          <span>Regras de layout</span>
          <TagEditor value={form.layout_rules} onChange={(v) => set("layout_rules", v)} placeholder="Ex: hierarquia limpa, margem de segurança…" />
        </div>
        <div className="field">
          <span>Regras de estilo de imagem</span>
          <TagEditor value={form.image_style_rules} onChange={(v) => set("image_style_rules", v)} placeholder="Ex: fotografia profissional, alto contraste…" />
        </div>
        <div className="field">
          <span>Notas de uso do logo</span>
          <TagEditor value={form.logo_usage_notes} onChange={(v) => set("logo_usage_notes", v)} placeholder="Ex: fundo claro, versão invertida…" />
        </div>
      </ProfileSection>

      {/* Salvar */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 8 }}>
        <button onClick={handleSave} disabled={saving}>
          {saving ? "Salvando…" : saved ? "Salvo ✓" : "Salvar todas as alterações"}
        </button>
        {error && <span style={{ fontSize: 13, color: "var(--danger)" }}>{error}</span>}
      </div>
    </section>
  );
}

// ── ProfileSection ────────────────────────────────────────────────────────────

function ProfileSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="profile-section">
      <h4 className="profile-section-title">{title}</h4>
      <div className="profile-section-body">{children}</div>
    </div>
  );
}

// ── TagEditor ─────────────────────────────────────────────────────────────────

function TagEditor({
  value,
  onChange,
  placeholder,
}: {
  value: string[];
  onChange: (v: string[]) => void;
  placeholder?: string;
}) {
  const [input, setInput] = useState("");

  function add() {
    const trimmed = input.trim();
    if (trimmed && !value.includes(trimmed)) {
      onChange([...value, trimmed]);
    }
    setInput("");
  }

  function remove(i: number) {
    onChange(value.filter((_, idx) => idx !== i));
  }

  return (
    <div className="tag-editor">
      {value.length > 0 && (
        <div className="chip-list" style={{ marginBottom: 8 }}>
          {value.map((item, i) => (
            <span key={i} className="chip chip-removable">
              {item}
              <button className="chip-remove" onClick={() => remove(i)} title="Remover">×</button>
            </span>
          ))}
        </div>
      )}
      <div className="tag-editor-input-row">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); add(); } }}
          placeholder={placeholder}
          style={{ flex: 1 }}
        />
        <button className="btn-ghost btn-sm" onClick={add} disabled={!input.trim()}>
          Adicionar
        </button>
      </div>
    </div>
  );
}
