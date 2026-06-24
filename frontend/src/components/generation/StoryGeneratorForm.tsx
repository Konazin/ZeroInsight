import { useEffect, useRef, useState } from "react";
import { Bookmark, BookmarkCheck, Check, ChevronLeft, ChevronRight, Eye, FolderOpen, PackageCheck, Tags, Timer, Trash2 } from "lucide-react";
import { api } from "../../lib/api";
import type { BrandItem, PromptTemplate } from "../../types";

// ── Types ─────────────────────────────────────────────────────────────────────

type StepIndex = 0 | 1 | 2 | 3;
type Feedback = { text: string; kind: "info" | "success" | "error" } | null;
type GenerateResult = {
  ok?: boolean;
  manifest?: {
    status?: string;
    outputs?: {
      directory?: string;
      images?: string[];
      base_images?: string[];
      review?: string;
    };
    validation?: { ok?: boolean; errors?: string[]; warnings?: string[] };
    ai_providers_used?: { image?: string; image_fallback?: string | null };
  };
};

const STEP_LABELS = ["Marca", "Briefing", "Prompt", "Gerar"];

const DEFAULTS = {
  topic: "RPV Federal",
  objective: "orientar com clareza",
  audience: "público jurídico",
  tone: "claro e responsável",
  cta: "Fale com a Requisite",
  visualIdea: "ambiente institucional limpo",
};

// ── Root component ────────────────────────────────────────────────────────────

export function StoryGeneratorForm() {
  const [step, setStep] = useState<StepIndex>(0);
  const [brands, setBrands] = useState<BrandItem[]>([]);

  // Step 0 — brand
  const [selectedBrand, setSelectedBrand] = useState<BrandItem | null>(null);

  // Step 1 — briefing
  const [topic, setTopic] = useState(DEFAULTS.topic);
  const [slides, setSlides] = useState(3);
  const [objective, setObjective] = useState(DEFAULTS.objective);
  const [audience, setAudience] = useState(DEFAULTS.audience);
  const [tone, setTone] = useState(DEFAULTS.tone);
  const [cta, setCta] = useState(DEFAULTS.cta);
  const [companySummary, setCompanySummary] = useState("");
  const [visualIdea, setVisualIdea] = useState(DEFAULTS.visualIdea);

  // Step 2 — prompt preview
  const [prompt, setPrompt] = useState("");
  const [promptEdited, setPromptEdited] = useState(false); // true só quando o usuário edita manualmente
  const [manualMode, setManualMode] = useState(false); // true = prompt manual sem injeções
  const [loadingPrompt, setLoadingPrompt] = useState(false);
  const [promptFeedback, setPromptFeedback] = useState<Feedback>(null);
  const promptGenerated = useRef(false);

  // Step 3 — generate
  const [imageProvider, setImageProvider] = useState<"openai" | "mock">("openai");
  const [generating, setGenerating] = useState(false);
  const [genFeedback, setGenFeedback] = useState<Feedback>(null);
  const [genResult, setGenResult] = useState<GenerateResult | null>(null);

  useEffect(() => {
    void api.brands().then(setBrands).catch(() => {});
  }, []);

  // Auto-generate prompt on first entry to step 2 (somente no modo assistido)
  useEffect(() => {
    if (step === 2 && !manualMode && !promptGenerated.current) {
      promptGenerated.current = true;
      void doGeneratePrompt();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [step, manualMode]);

  async function doGeneratePrompt() {
    setLoadingPrompt(true);
    setPromptEdited(false); // reset: novo auto-gerado não conta como edição manual
    setPromptFeedback({ text: "Gerando prompt com IA…", kind: "info" });
    try {
      const res = await api.imagePreview({
        topic: topic.trim(),
        objective,
        audience,
        tone,
        cta,
        visual_idea: visualIdea,
        brand_profile_id: selectedBrand?.id ?? null,
      }) as { prompt?: string };
      setPrompt(res.prompt ?? "");
      setPromptFeedback({ text: "Prévia do prompt — edite para personalizar ou avance para gerar.", kind: "info" });
    } catch (err) {
      setPromptFeedback({
        text: err instanceof Error ? err.message : "Falha ao gerar prompt.",
        kind: "error",
      });
    } finally {
      setLoadingPrompt(false);
    }
  }

  function regenPrompt() {
    setPrompt("");
    setPromptEdited(false);
    promptGenerated.current = true;
    void doGeneratePrompt();
  }

  async function doGenerate() {
    setGenerating(true);
    setGenFeedback({ text: "Enviando para geração…", kind: "info" });
    setGenResult(null);
    try {
      const res = await api.generateStory({
        topic: topic.trim(),
        objective,
        audience,
        tone,
        cta,
        slides,
        company_summary: companySummary,
        brand_profile_id: selectedBrand?.id ?? null,
        // Envia custom_image_prompt se: modo manual OU usuário editou manualmente.
        // No modo assistido sem edição, o runner usa build_full_composition_prompt() por slide.
        custom_image_prompt: (manualMode || promptEdited) && prompt.trim() ? prompt.trim() : null,
        ai_image_provider: imageProvider,
      }) as GenerateResult;
      setGenResult(res);
      const ok = res.manifest?.validation?.ok ?? res.ok;
      setGenFeedback(
        ok
          ? { text: "Pacote gerado com sucesso!", kind: "success" }
          : { text: "Geração concluída com advertências — verifique os detalhes abaixo.", kind: "error" }
      );
    } catch (err) {
      setGenFeedback({
        text: err instanceof Error ? err.message : "Falha ao gerar pacote.",
        kind: "error",
      });
    } finally {
      setGenerating(false);
    }
  }

  function goTo(s: StepIndex) {
    if (s < 2) {
      promptGenerated.current = false;
      setManualMode(false);
      setPromptEdited(false);
    }
    setStep(s);
  }

  function handleSetVisualIdea(v: string) {
    setVisualIdea(v);
    promptGenerated.current = false;
  }

  return (
    <div>
      <div className="page-header">
        <h1 className="page-header-title">Gerar Stories</h1>
        <p className="page-header-desc">Crie um pacote de stories para Instagram em 4 etapas — marca, briefing, prompt e geração.</p>
      </div>
      <section className="panel">
      <StepBar
        current={step}
        labels={STEP_LABELS}
        onClickStep={(i) => i < step && goTo(i as StepIndex)}
      />

      {step === 0 && (
        <Step0Brand
          brands={brands}
          selected={selectedBrand}
          onSelect={setSelectedBrand}
          onNext={() => goTo(1)}
        />
      )}

      {step === 1 && (
        <Step1Briefing
          topic={topic} setTopic={setTopic}
          slides={slides} setSlides={setSlides}
          objective={objective} setObjective={setObjective}
          audience={audience} setAudience={setAudience}
          tone={tone} setTone={setTone}
          cta={cta} setCta={setCta}
          visualIdea={visualIdea} setVisualIdea={handleSetVisualIdea}
          companySummary={companySummary} setCompanySummary={setCompanySummary}
          onPrev={() => goTo(0)}
          onNext={() => goTo(2)}
        />
      )}

      {step === 2 && (
        <Step2Prompt
          prompt={prompt}
          setPrompt={(v) => { setPrompt(v); setPromptEdited(true); }}
          promptEdited={promptEdited}
          manualMode={manualMode}
          setManualMode={(v) => {
            setManualMode(v);
            if (v) {
              // Entrando em modo manual: limpa prompt gerado e para gerações futuras
              setPrompt("");
              setPromptEdited(false);
              setPromptFeedback(null);
            } else {
              // Voltando para modo assistido: regenera
              promptGenerated.current = false;
              setPrompt("");
              setPromptEdited(false);
              void doGeneratePrompt();
            }
          }}
          loading={loadingPrompt}
          feedback={promptFeedback}
          setFeedback={setPromptFeedback}
          visualIdea={visualIdea}
          setVisualIdea={handleSetVisualIdea}
          topic={topic}
          slides={slides}
          selectedBrandId={selectedBrand?.id ?? null}
          brands={brands}
          onRegen={regenPrompt}
          onPrev={() => goTo(1)}
          onNext={() => goTo(3)}
        />
      )}

      {step === 3 && (
        <Step3Generate
          brand={selectedBrand}
          topic={topic}
          slides={slides}
          audience={audience}
          tone={tone}
          cta={cta}
          imageProvider={imageProvider}
          setImageProvider={setImageProvider}
          generating={generating}
          feedback={genFeedback}
          result={genResult}
          onGenerate={doGenerate}
          onReset={() => { setGenResult(null); setGenFeedback(null); }}
          onPrev={() => goTo(2)}
        />
      )}
      </section>
    </div>
  );
}

// ── StepBar ───────────────────────────────────────────────────────────────────

function StepBar({
  current,
  labels,
  onClickStep,
}: {
  current: number;
  labels: string[];
  onClickStep: (i: number) => void;
}) {
  return (
    <div className="step-bar">
      {labels.map((label, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <div key={i} className="step-bar-segment">
            <button
              className={`step-node${done ? " done" : active ? " active" : ""}`}
              onClick={() => onClickStep(i)}
              disabled={!done}
              title={done ? `Voltar para ${label}` : undefined}
            >
              <span className="step-circle">
                {done ? <Check size={13} /> : i + 1}
              </span>
              <span className="step-node-label">{label}</span>
            </button>
            {i < labels.length - 1 && (
              <div className={`step-connector${done ? " done" : ""}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Step 0 — Marca ────────────────────────────────────────────────────────────

function Step0Brand({
  brands,
  selected,
  onSelect,
  onNext,
}: {
  brands: BrandItem[];
  selected: BrandItem | null;
  onSelect: (b: BrandItem | null) => void;
  onNext: () => void;
}) {
  return (
    <div>
      <div className="wizard-step-header">
        <h3 className="wizard-step-title">Qual marca você quer usar?</h3>
        <p className="wizard-step-desc">
          A marca define identidade visual, tom e cores dos stories. Você pode pular e usar as configurações padrão.
        </p>
      </div>

      <div className="brand-picker">
        <button
          className={`brand-card${selected === null ? " selected" : ""}`}
          onClick={() => onSelect(null)}
        >
          <span className="brand-card-icon"><Tags size={16} /></span>
          <span className="brand-card-name">Sem marca</span>
          <span className="brand-card-hint">Configuração padrão do sistema</span>
        </button>

        {brands.map((b) => (
          <button
            key={b.id}
            className={`brand-card${selected?.id === b.id ? " selected" : ""}`}
            onClick={() => onSelect(selected?.id === b.id ? null : b)}
          >
            <span className="brand-card-icon">{b.name.charAt(0).toUpperCase()}</span>
            <span className="brand-card-name">{b.name}</span>
            <span className="brand-card-hint">{b.path.split(/[\\/]/).pop()}</span>
          </button>
        ))}
      </div>

      {brands.length === 0 && (
        <p style={{ fontSize: 13, color: "var(--text-subtle)", marginTop: 12, padding: "10px 14px", background: "var(--bg-elevated)", borderRadius: 8, border: "1px solid var(--border-subtle)" }}>
          Nenhuma marca importada ainda. Vá em <strong>Biblioteca → Marcas</strong> para adicionar.
        </p>
      )}

      <div className="wizard-nav" style={{ justifyContent: "flex-end" }}>
        <button onClick={onNext}>
          Continuar para briefing <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}

// ── Step 1 — Briefing ─────────────────────────────────────────────────────────

function Step1Briefing(props: {
  topic: string; setTopic: (v: string) => void;
  slides: number; setSlides: (v: number) => void;
  objective: string; setObjective: (v: string) => void;
  audience: string; setAudience: (v: string) => void;
  tone: string; setTone: (v: string) => void;
  cta: string; setCta: (v: string) => void;
  visualIdea: string; setVisualIdea: (v: string) => void;
  companySummary: string; setCompanySummary: (v: string) => void;
  onPrev: () => void;
  onNext: () => void;
}) {
  const canNext = props.topic.trim().length > 0;

  return (
    <div>
      <div className="wizard-step-header">
        <h3 className="wizard-step-title">Sobre o que é esse story?</h3>
        <p className="wizard-step-desc">
          Preencha o tema principal e as informações de contexto. Campos em branco usam os valores sugeridos.
        </p>
      </div>

      {/* Seção 1 — Tema */}
      <div className="form-section">
        <div className="form-section-label">Tema e mensagem</div>
        <div className="form-section-grid">
          <label className="field full">
            <span>
              Tema principal{" "}
              <span style={{ color: "var(--danger)", fontWeight: 400, textTransform: "none" }}>*</span>
            </span>
            <input
              value={props.topic}
              onChange={(e) => props.setTopic(e.target.value)}
              placeholder="Ex: RPV Federal"
              autoFocus
            />
          </label>
          <label className="field">
            <span>Objetivo</span>
            <input
              value={props.objective}
              onChange={(e) => props.setObjective(e.target.value)}
              placeholder={DEFAULTS.objective}
            />
          </label>
          <label className="field">
            <span>Público-alvo</span>
            <input
              value={props.audience}
              onChange={(e) => props.setAudience(e.target.value)}
              placeholder={DEFAULTS.audience}
            />
          </label>
        </div>
      </div>

      {/* Seção 2 — Visual e formato */}
      <div className="form-section">
        <div className="form-section-label">Visual e formato</div>
        <div className="form-section-grid">
          <label className="field">
            <span>Tom de voz</span>
            <input
              value={props.tone}
              onChange={(e) => props.setTone(e.target.value)}
              placeholder={DEFAULTS.tone}
            />
          </label>
          <label className="field">
            <span>Ideia visual</span>
            <input
              value={props.visualIdea}
              onChange={(e) => props.setVisualIdea(e.target.value)}
              placeholder={DEFAULTS.visualIdea}
            />
          </label>
          <label className="field">
            <span>CTA (chamada para ação)</span>
            <input
              value={props.cta}
              onChange={(e) => props.setCta(e.target.value)}
              placeholder={DEFAULTS.cta}
            />
          </label>
          <label className="field">
            <span>Número de slides</span>
            <input
              type="number" min={1} max={10} value={props.slides}
              onChange={(e) =>
                props.setSlides(Math.max(1, Math.min(10, Number(e.target.value))))
              }
            />
          </label>
        </div>
      </div>

      {/* Seção 3 — Contexto opcional */}
      <div className="form-section">
        <div className="form-section-label">Contexto da empresa <span style={{ fontWeight: 400, textTransform: "none", letterSpacing: 0, fontSize: 10, color: "var(--text-subtle)" }}>(opcional)</span></div>
        <label className="field" style={{ margin: 0 }}>
          <textarea
            value={props.companySummary}
            onChange={(e) => props.setCompanySummary(e.target.value)}
            rows={3}
            placeholder="Descreva brevemente o que a empresa faz, seus diferenciais ou público. Usado para enriquecer o conteúdo gerado."
            style={{ resize: "vertical" }}
          />
        </label>
      </div>

      <div className="wizard-nav">
        <button className="btn-ghost" onClick={props.onPrev}>
          <ChevronLeft size={16} /> Voltar
        </button>
        <button onClick={props.onNext} disabled={!canNext}>
          Ver prompt de imagem <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}

// ── Step 2 — Prompt preview ───────────────────────────────────────────────────

function Step2Prompt(props: {
  prompt: string;
  setPrompt: (v: string) => void;
  promptEdited: boolean;
  manualMode: boolean;
  setManualMode: (v: boolean) => void;
  loading: boolean;
  feedback: Feedback;
  setFeedback: (f: Feedback) => void;
  visualIdea: string;
  setVisualIdea: (v: string) => void;
  topic: string;
  slides: number;
  selectedBrandId: string | null;
  brands: BrandItem[];
  onRegen: () => void;
  onPrev: () => void;
  onNext: () => void;
}) {
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [showLoad, setShowLoad] = useState(false);
  const [showSave, setShowSave] = useState(false);
  const [saveName, setSaveName] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    void api.prompts().then(setTemplates).catch(() => {});
  }, []);

  async function handleSave() {
    if (!saveName.trim()) return;
    if (!props.prompt.trim()) {
      props.setFeedback({ text: "O prompt está vazio — gere ou escreva um prompt antes de salvar.", kind: "error" });
      return;
    }
    setSaving(true);
    try {
      const t = await api.savePrompt({
        name: saveName.trim(),
        prompt: props.prompt.trim(),
        brand_id: props.selectedBrandId,
      });
      setTemplates((prev) => [t, ...prev]);
      setSaveName("");
      setShowSave(false);
      props.setFeedback({ text: `Template "${t.name}" salvo.`, kind: "success" });
    } catch (err) {
      props.setFeedback({ text: err instanceof Error ? err.message : "Falha ao salvar template.", kind: "error" });
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(id: string, e: React.MouseEvent) {
    e.stopPropagation();
    await api.deletePrompt(id);
    setTemplates((prev) => prev.filter((t) => t.id !== id));
  }

  function loadTemplate(t: PromptTemplate) {
    props.setPrompt(t.prompt); // já dispara setPromptEdited(true) via wrapper no pai
    setShowLoad(false);
    props.setFeedback({ text: `Template "${t.name}" carregado — será usado como prompt fixo.`, kind: "success" });
  }

  const brandName = props.selectedBrandId
    ? (props.brands.find((b) => b.id === props.selectedBrandId)?.name ?? props.selectedBrandId)
    : null;

  return (
    <div>
      <div className="wizard-step-header">
        <h3 className="wizard-step-title">
          Prompt de imagem
          {props.manualMode && (
            <span style={{ marginLeft: 10, fontSize: 12, fontWeight: 400, color: "var(--accent)", background: "rgba(99,102,241,0.12)", padding: "2px 8px", borderRadius: 6 }}>
              modo manual
            </span>
          )}
          {!props.manualMode && props.promptEdited && (
            <span style={{ marginLeft: 10, fontSize: 12, fontWeight: 400, color: "var(--warning)", background: "rgba(245,158,11,0.12)", padding: "2px 8px", borderRadius: 6 }}>
              editado manualmente
            </span>
          )}
        </h3>
        <p className="wizard-step-desc">
          {props.manualMode
            ? "Prompt manual — enviado diretamente à IA, sem injeções de marca ou perfil. Você controla tudo."
            : props.promptEdited
              ? "Prompt personalizado — será enviado exatamente como está para todos os slides."
              : brandName
                ? <>Prévia do prompt gerado com base em <strong>{brandName}</strong>. A IA vai personalizar por slide. Edite para sobrescrever.</>
                : "Prévia do prompt. A IA vai personalizar o conteúdo por slide. Edite para sobrescrever com um prompt fixo."}
        </p>
      </div>

      {/* Seletor de modo */}
      <div className="prompt-mode-bar">
        <button
          className={`prompt-mode-btn${!props.manualMode ? " active" : ""}`}
          onClick={() => props.setManualMode(false)}
          disabled={props.loading}
        >
          <Eye size={13} /> Assistido por IA
        </button>
        <button
          className={`prompt-mode-btn${props.manualMode ? " active" : ""}`}
          onClick={() => props.setManualMode(true)}
          disabled={props.loading}
        >
          Prompt manual
        </button>
      </div>

      <div className="split" style={{ marginTop: 0 }}>
        {/* Left — prompt editor */}
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {/* Visual idea + regen row — só no modo assistido */}
          {!props.manualMode && (
            <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
              <label className="field" style={{ marginBottom: 0, flex: 1 }}>
                <span>Ideia visual</span>
                <input
                  value={props.visualIdea}
                  onChange={(e) => props.setVisualIdea(e.target.value)}
                />
              </label>
              <button
                className="btn-ghost btn-sm"
                onClick={props.onRegen}
                disabled={props.loading}
                style={{ flexShrink: 0, height: 38, alignSelf: "flex-end" }}
              >
                <Eye size={14} /> {props.loading ? "Gerando…" : "Regerar com IA"}
              </button>
            </div>
          )}

          {/* Editable textarea */}
          <textarea
            className="prompt-preview"
            value={props.loading ? "Gerando prompt com IA…" : props.prompt}
            onChange={(e) => !props.loading && props.setPrompt(e.target.value)}
            readOnly={props.loading}
            placeholder={props.manualMode
              ? "Escreva seu prompt completo aqui. Ele será enviado diretamente à IA sem nenhuma modificação."
              : "O prompt aparecerá aqui. Você também pode escrever um prompt manual."}
            style={{ flex: 1, opacity: props.loading ? 0.5 : 1, minHeight: 260, resize: "vertical" }}
            autoFocus={props.manualMode}
          />

          {/* Toolbar */}
          <div className="prompt-toolbar">
            {/* Save section */}
            {showSave ? (
              <div className="prompt-save-form">
                <input
                  className="prompt-save-input"
                  placeholder="Nome do template…"
                  value={saveName}
                  onChange={(e) => setSaveName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && void handleSave()}
                  autoFocus
                />
                <button className="btn-sm" onClick={() => void handleSave()} disabled={saving || !saveName.trim()}>
                  {saving ? "…" : "Salvar"}
                </button>
                <button className="btn-ghost btn-sm" onClick={() => { setShowSave(false); setSaveName(""); }}>
                  Cancelar
                </button>
              </div>
            ) : (
              <button
                className="btn-ghost btn-sm"
                onClick={() => { setShowSave(true); setShowLoad(false); }}
                disabled={!props.prompt.trim()}
                title="Salvar prompt atual como template"
              >
                <Bookmark size={14} /> Salvar template
              </button>
            )}

            {/* Load section */}
            <div style={{ position: "relative" }}>
              <button
                className="btn-ghost btn-sm"
                onClick={() => { setShowLoad((v) => !v); setShowSave(false); }}
                title="Carregar um template salvo"
              >
                <BookmarkCheck size={14} />
                Carregar template
                {templates.length > 0 && (
                  <span className="badge">{templates.length}</span>
                )}
              </button>

              {showLoad && (
                <div className="prompt-templates-dropdown">
                  {templates.length === 0 ? (
                    <p className="prompt-templates-empty">Nenhum template salvo.</p>
                  ) : (
                    templates.map((t) => (
                      <div key={t.id} className="prompt-template-item" onClick={() => loadTemplate(t)}>
                        <div className="prompt-template-meta">
                          <span className="prompt-template-name">{t.name}</span>
                          {t.brand_id && (
                            <span className="prompt-template-brand">
                              {props.brands.find((b) => b.id === t.brand_id)?.name ?? t.brand_id}
                            </span>
                          )}
                        </div>
                        <p className="prompt-template-preview">{t.prompt.slice(0, 80)}…</p>
                        <button
                          className="prompt-template-delete"
                          onClick={(e) => void handleDelete(t.id, e)}
                          title="Excluir template"
                        >
                          <Trash2 size={12} />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          </div>

          {props.feedback && (
            <p className={`feedback ${props.feedback.kind}`} style={{ margin: 0 }}>
              {props.feedback.text}
            </p>
          )}
        </div>

        {/* Right — 9:16 preview */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
          <div className="story-preview">
            <div className="safe top" />
            <div className="safe center">
              <p style={{
                margin: "6px 8px",
                color: "rgba(255,255,255,0.5)",
                fontSize: 11,
                fontStyle: "italic",
                lineHeight: 1.4,
              }}>
                {props.topic}
              </p>
            </div>
            <div className="safe bottom" />
          </div>
          <p style={{ margin: 0, fontSize: 11, color: "var(--text-subtle)", textAlign: "center" }}>
            Formato 9:16 · {props.slides} slide{props.slides !== 1 ? "s" : ""}
          </p>
        </div>
      </div>

      <div className="wizard-nav">
        <button className="btn-ghost" onClick={props.onPrev}>
          <ChevronLeft size={16} /> Voltar
        </button>
        <button onClick={props.onNext} disabled={props.loading}>
          Revisar e gerar <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
}

// ── Step 3 — Generate ─────────────────────────────────────────────────────────

function Step3Generate(props: {
  brand: BrandItem | null;
  topic: string;
  slides: number;
  audience: string;
  tone: string;
  cta: string;
  imageProvider: "openai" | "mock";
  setImageProvider: (v: "openai" | "mock") => void;
  generating: boolean;
  feedback: Feedback;
  result: GenerateResult | null;
  onGenerate: () => void;
  onReset: () => void;
  onPrev: () => void;
}) {
  const [elapsed, setElapsed] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (props.generating) {
      setElapsed(0);
      timerRef.current = setInterval(() => setElapsed((s) => s + 1), 1000);
    } else {
      if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [props.generating]);

  const outputs = props.result?.manifest?.outputs;
  const validation = props.result?.manifest?.validation;
  const images = outputs?.images ?? [];
  const providerUsed = props.result?.manifest?.ai_providers_used?.image;

  return (
    <div>
      <div className="wizard-step-header">
        <h3 className="wizard-step-title">Tudo pronto para gerar</h3>
        <p className="wizard-step-desc">
          Revise o resumo e escolha o provedor de imagem. Após gerar, as imagens aparecem logo abaixo.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 0 }}>
        <div className="gen-summary">
          <SummaryRow label="Marca"  value={props.brand?.name ?? "Sem marca"} />
          <SummaryRow label="Tema"   value={props.topic} />
          <SummaryRow label="Slides" value={`${props.slides} slide${props.slides !== 1 ? "s" : ""}`} />
        </div>
        <div className="gen-summary">
          <SummaryRow label="Público" value={props.audience} />
          <SummaryRow label="Tom"     value={props.tone} />
          <SummaryRow label="CTA"     value={props.cta} />
        </div>
      </div>

      {/* Provider picker */}
      {!props.result && (
        <div className="gen-provider-picker">
          <span className="gen-provider-label">Provedor de imagem</span>
          <label className={`gen-provider-option${props.imageProvider === "openai" ? " selected" : ""}`}>
            <input
              type="radio"
              name="imgProvider"
              value="openai"
              checked={props.imageProvider === "openai"}
              onChange={() => props.setImageProvider("openai")}
            />
            <span className="gen-provider-name">OpenAI</span>
            <span className="gen-provider-hint">gpt-image-2 · requer chave API</span>
          </label>
          <label className={`gen-provider-option${props.imageProvider === "mock" ? " selected" : ""}`}>
            <input
              type="radio"
              name="imgProvider"
              value="mock"
              checked={props.imageProvider === "mock"}
              onChange={() => props.setImageProvider("mock")}
            />
            <span className="gen-provider-name">Mock</span>
            <span className="gen-provider-hint">Gradiente local · sem API · rápido</span>
          </label>
        </div>
      )}

      {!props.result && (
        <button
          onClick={props.onGenerate}
          disabled={props.generating}
          style={{ marginTop: 20, width: "100%", justifyContent: "center", padding: "13px 24px", fontSize: 15, fontWeight: 700, borderRadius: 10, boxShadow: "0 4px 20px rgba(124,58,237,0.35)" }}
        >
          <PackageCheck size={17} />
          {props.generating ? "Gerando pacote…" : "Gerar stories agora"}
        </button>
      )}

      {/* Cronômetro durante a geração */}
      {props.generating && (
        <div className="gen-timer">
          <Timer size={14} />
          <span>Aguardando resposta da IA… <strong>{formatElapsed(elapsed)}</strong></span>
          <span className="gen-timer-hint">A geração de imagem pode levar alguns minutos. Não feche esta aba.</span>
        </div>
      )}

      {props.feedback && (
        <p className={`feedback ${props.feedback.kind}`} style={{ marginTop: 12 }}>{props.feedback.text}</p>
      )}

      {/* Resultado */}
      {props.result && outputs && (
        <div className="gen-result">
          {/* Header com validação */}
          <div className="gen-result-header">
            <span className={`gen-result-badge ${validation?.ok ? "ok" : "warn"}`}>
              {validation?.ok ? "✓ Validado" : "⚠ Com advertências"}
            </span>
            {providerUsed && (
              <span className="gen-result-provider">via {providerUsed}</span>
            )}
          </div>

          {/* Pasta de saída */}
          {outputs.directory && (
            <div className="gen-result-path">
              <FolderOpen size={14} />
              <code>{outputs.directory}</code>
              <button
                className="btn-ghost btn-sm"
                onClick={() => void api.openFolder(outputs.directory!)}
                title="Abrir no explorador de arquivos"
              >
                Abrir pasta
              </button>
            </div>
          )}

          {/* Imagens geradas */}
          {images.length > 0 && (
            <div style={{ marginTop: 14 }}>
              <p className="gen-result-section-label">
                Imagens geradas ({images.length})
              </p>
              <div className="gen-result-images">
                {images.map((imgPath, i) => (
                  <a
                    key={i}
                    href={api.fileUrl(imgPath)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="gen-result-image-thumb"
                    title={imgPath.split(/[\\/]/).pop()}
                  >
                    <img
                      src={api.fileUrl(imgPath)}
                      alt={`Story ${i + 1}`}
                      loading="lazy"
                    />
                    <span className="gen-result-image-label">Slide {i + 1}</span>
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Erros e avisos */}
          {(validation?.errors?.length || validation?.warnings?.length) ? (
            <div style={{ marginTop: 12 }}>
              {validation?.errors?.map((e, i) => (
                <p key={i} className="feedback error" style={{ margin: "4px 0" }}>✗ {e}</p>
              ))}
              {validation?.warnings?.map((w, i) => (
                <p key={i} className="feedback info" style={{ margin: "4px 0" }}>⚠ {w}</p>
              ))}
            </div>
          ) : null}

          <div style={{ marginTop: 14 }}>
            <button className="btn-ghost btn-sm" onClick={props.onReset}>
              Gerar novamente
            </button>
          </div>
        </div>
      )}

      <div className="wizard-nav">
        <button className="btn-ghost" onClick={props.onPrev} disabled={props.generating}>
          <ChevronLeft size={16} /> Voltar
        </button>
      </div>
    </div>
  );
}

function formatElapsed(s: number): string {
  if (s < 60) return `${s}s`;
  return `${Math.floor(s / 60)}m ${s % 60}s`;
}

// ── SummaryRow ────────────────────────────────────────────────────────────────

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="summary-row">
      <span className="summary-label">{label}</span>
      <span className="summary-value">{value}</span>
    </div>
  );
}
