# ZeroInsight

> Plataforma de automação de conteúdo com IA para marketing jurídico — gera Instagram Stories completos com texto, identidade visual e logotipo embutidos diretamente pela IA.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![React](https://img.shields.io/badge/React-19-61dafb)
![FastAPI](https://img.shields.io/badge/FastAPI-0.11x-009688)
![OpenAI](https://img.shields.io/badge/OpenAI-gpt--image--2-412991)
![License](https://img.shields.io/badge/License-MIT-green)

---

## O que é

O ZeroInsight é uma aplicação local (backend Python + frontend React) que automatiza a criação de pacotes de Instagram Stories institucionais para escritórios jurídicos e legaltechs. Dado um briefing, ele:

1. Gera o roteiro de slides com IA de texto
2. Monta o prompt visual completo baseado no BrandProfile da empresa
3. Envia a logo da marca junto ao prompt para o modelo de imagem (`gpt-image-2`) via `/images/edit`, que a integra ao design gerado
4. Exporta os PNGs finais, `manifest.json` e página de revisão HTML

---

## Stack

| Camada | Tecnologia |
|--------|------------|
| Backend | Python 3.10+, FastAPI, Uvicorn |
| Frontend | React 19, TypeScript, Vite 6 |
| Imagem IA | OpenAI `gpt-image-2` via `/images/generate` e `/images/edit` |
| Texto IA | OpenAI, Groq, provider custom OpenAI-compatible ou mock |
| Renderização | Pillow (contador de slide; texto gerado pela própria IA) |
| Browser | Playwright + CDP (Brave, opcional para métricas Dino) |

---

## Início rápido

### Pré-requisitos (Windows)

Instale com o **winget** (Prompt de Comando ou PowerShell):

```bat
winget install Python.Python.3.12
winget install OpenJS.NodeJS.LTS
```

Reinicie o terminal após instalar para que `python` e `npm` fiquem no PATH.

### Windows (recomendado)

```bat
start.bat
```

O script cria o `.venv` automaticamente, instala todas as dependências Python, verifica o Node.js e inicia backend + frontend.

### Manual

```bash
# Backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

python start.py          # inicia backend (porta 8765) e abre o frontend

# Frontend (em outro terminal)
cd frontend
npm install
npm run dev              # porta 5173
```

Acesse `http://127.0.0.1:5173`.

---

## Funcionalidades

### Gerador de Stories (wizard 4 etapas)

| Etapa | O que faz |
|-------|-----------|
| **1 — Marca** | Seleciona o BrandProfile (ou "sem marca") |
| **2 — Briefing** | Tema, objetivo, público, tom, CTA, número de slides, ideia visual |
| **3 — Prompt** | Prévia do prompt gerado pela IA; modo **Assistido** ou **Manual** |
| **4 — Gerar** | Escolhe provedor de imagem e dispara a pipeline |

**Modo assistido:** a aplicação monta um prompt completo por slide com injeção de cores, estilo e regras do BrandProfile. Edições feitas pelo usuário são aplicadas como direção visual sem substituir o título, corpo e CTA específicos de cada slide.

**Modo manual:** o textarea fica em branco; o texto do usuário é a direção principal enviada ao modelo. Antes do envio, o backend valida termos proibidos e acrescenta apenas as regras obrigatórias de compliance do provider.

Templates de prompt podem ser salvos e carregados em qualquer geração futura.

### Geração de imagem com IA

- Usa `gpt-image-2` no formato `1024x1536` (9:16 vertical)
- Quando há logo cadastrada: cria canvas transparente com a logo posicionada no canto superior esquerdo e usa `/images/edit` — o modelo preserva a logo e gera a composição ao redor
- Quando não há logo: usa `/images/generate` com descrição textual da marca
- A imagem final já contém título, corpo e CTA renderizados pela IA; o Pillow só adiciona o contador de slide

### BrandProfile

Cada marca tem um perfil JSON completo editável pela UI:

| Seção | Campos |
|-------|--------|
| Identidade | Nome, resumo da empresa |
| Tom e audiência | Tom de voz, público-alvo, estilo de CTA |
| Linguagem | Termos preferidos, termos proibidos |
| Conformidade | Regras de conteúdo, regras de compliance |
| Visual | Logo (upload), paleta de cores, estilo visual, tipografia, layout, estilo de imagem, uso do logo |

Importação de BrandProfile a partir de PDF ou DOCX via `/brands/import`.

### Providers de IA

| Tipo | Providers disponíveis |
|------|-----------------------|
| Texto | `openai`, `groq`, `custom` (OpenAI-compatible), `mock` |
| Imagem | `openai` (`gpt-image-2`), `custom`, `local`, `mock` |
| Visão | `openai`, `groq`, `custom`, `mock` |

O provider `custom` aceita qualquer API no formato OpenAI-compatible (`/chat/completions` para texto, `b64_json` ou `url` para imagem).

---

## Arquitetura

```
ZeroInsight/
├── start.bat / start.py          # inicialização Windows
├── zero_insight/
│   ├── config/                   # Settings e .env
│   ├── ai_providers/             # OpenAI, Groq, custom, mock, local
│   ├── brand/                    # BrandProfile, validator, cache
│   ├── browser/                  # CDP + extração Dino (opcional)
│   ├── capture/                  # Screenshot Playwright
│   ├── content/                  # StoryBrief, StorySlide, script planner
│   ├── image/                    # prompt_builder (build_full_composition_prompt)
│   ├── pipeline/                 # story_runner, runner
│   ├── render/                   # StoryRenderer (Pillow)
│   ├── qa/                       # validação de pacote
│   └── server/
│       ├── app.py                # FastAPI app
│       ├── routes/               # brands, generation, outputs, providers,
│       │                         #   settings, prompts, brave, health
│       └── schemas/              # Pydantic schemas
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── brand/            # BrandProfileEditor, BrandImportPanel
│   │   │   ├── generation/       # StoryGeneratorForm, PostGeneratorForm
│   │   │   ├── providers/        # ProviderSettings, ProviderTestPanel
│   │   │   └── settings/         # SettingsPanel
│   │   ├── pages/                # Dashboard, Brands, Outputs, Logs
│   │   ├── lib/api.ts            # cliente HTTP
│   │   └── types.ts              # tipos TypeScript
│   └── vite.config.ts
├── requirements.txt
├── .env.example
└── LICENSE
```

---

## Configuração

```bash
copy .env.example .env
```

Variáveis principais do `.env`:

| Variável | Descrição | Padrão |
|----------|-----------|--------|
| `OPENAI_API_KEY` | Chave OpenAI | — |
| `OPENAI_IMAGE_MODEL` | Modelo de imagem | `gpt-image-2` |
| `OPENAI_IMAGE_SIZE` | Tamanho da imagem | `1024x1536` |
| `OPENAI_IMAGE_QUALITY` | Qualidade | `medium` |
| `OPENAI_TEXT_MODEL` | Modelo de texto | `gpt-5.4-mini` |
| `DEFAULT_TEXT_PROVIDER` | Provider padrão de texto | `mock` |
| `DEFAULT_IMAGE_PROVIDER` | Provider padrão de imagem | `local` |
| `GROQ_API_KEY` | Chave Groq (opcional) | — |
| `CUSTOM_TEXT_BASE_URL` | Base URL provider custom texto | — |
| `CUSTOM_IMAGE_BASE_URL` | Base URL provider custom imagem | — |
| `ALLOW_EXTERNAL_AI_FOR_BRAND_DOCS` | Envia PDF/DOCX para IA externa | `false` |
| `CDP_PORT` | Porta debug Brave (Dino, opcional) | `9222` |
| `STORY_BRAND_NAME` | Marca padrão nos Stories | `Requisite` |
| `STORY_BRAND_PRIMARY_COLOR` | Cor primária mock | `#111827` |
| `STORY_BRAND_SECONDARY_COLOR` | Cor secundária mock | `#2563EB` |

> `.env` está no `.gitignore`. Nunca commite chaves de API.

---

## API

O backend roda em `http://127.0.0.1:8765`. Endpoints principais:

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/health` | Status do servidor |
| GET/POST | `/api/settings` | Leitura e gravação de configurações |
| GET | `/api/providers` | Providers disponíveis e ativos |
| POST | `/api/providers/test` | Testa provider por tipo e nome |
| GET | `/api/brands` | Lista BrandProfiles |
| GET | `/api/brands/{id}` | Detalhes do BrandProfile |
| PUT | `/api/brands/{id}` | Atualiza BrandProfile |
| POST | `/api/brands/{id}/logo` | Upload de logo (PNG/JPG/WEBP) |
| GET | `/api/brands/{id}/logo` | Serve a logo |
| POST | `/api/brands/import` | Importa PDF/DOCX como BrandProfile |
| POST | `/api/generate/story` | Gera pacote de Stories |
| POST | `/api/generate/post` | Gera post de blog |
| POST | `/api/generate/image-preview` | Retorna prompt de composição |
| GET | `/api/prompts` | Lista templates de prompt |
| POST | `/api/prompts` | Salva template |
| DELETE | `/api/prompts/{id}` | Remove template |
| GET | `/api/outputs` | Lista saídas geradas |
| POST | `/api/brave/start` | Inicia Brave com CDP |

---

## Saídas geradas

Cada geração de Stories produz uma pasta em `stories/`:

```
stories/
  YYYYMMDD_nome_campanha/
    manifest.json          # providers usados, validação, paths
    story_script.json      # roteiro completo por slide
    story_01_base.png      # imagem bruta da IA
    story_01.png           # imagem final (com contador)
    story_02_base.png
    story_02.png
    review.html            # página de revisão visual
```

O `manifest.json` registra providers, modelos, prompts usados, `revised_prompt` da OpenAI quando disponível, e resultado da validação de compliance da marca.

O campo `prompt_sent` registra o prompt efetivamente enviado em cada slide, enquanto `prompt` preserva o pacote de direção visual usado para auditoria.

---

## Testes

```bash
python -m unittest discover -s tests -p "test_*.py" -v
cd frontend && npm run lint && npm run build
cd ../mobile && npm run typecheck
```

---

## Conformidade e segurança

- Sem publicação automática no Instagram
- Login no Dino continua manual (sem bypass de captcha ou MFA)
- API keys apenas em `.env` local, nunca versionadas
- Documentos de marca só enviados a IA externa com `ALLOW_EXTERNAL_AI_FOR_BRAND_DOCS=true`
- Stories validados contra promessas absolutas ("garantido", "100% aprovado", "sem risco")
- Todo pacote fica em `AWAITING_REVIEW` até aprovação humana
- Logs não imprimem API keys nem conteúdo de documentos

---

## Licença

MIT — veja [LICENSE](LICENSE).
