# ZeroInsight

> Automação interna para coleta de métricas no dashboard Dino (sessão Brave autenticada), geração de posts jurídicos com Groq Vision e publicação assistida em Markdown.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Playwright](https://img.shields.io/badge/Playwright-CDP-green)
![Groq](https://img.shields.io/badge/Groq-Vision-orange)
![License](https://img.shields.io/badge/License-Uso%20restrito-red)

---

## Aviso legal e uso controlado

**Este software foi desenvolvido para a [RequisiteRPV LTDA](https://requisite.com.br) e o uso é controlado.**

- Uso permitido apenas para pessoas e ambientes **autorizados** pela empresa.
- Não é software livre / open source: consulte o arquivo [`LICENSE`](LICENSE).
- Não redistribua, não publique forks públicos e não compartilhe `.env`, chaves de API ou capturas de tela sem aprovação interna.
- O repositório pode existir no GitHub por conveniência operacional; isso **não** autoriza uso por terceiros.

---

## Visão geral

O **ZeroInsight** conecta ao **Brave** já logado (Chrome DevTools Protocol), extrai métricas do **dashboard Dino**, captura **screenshot** da página, envia dados + imagem para a **Groq (modelo com visão)** e gera um **post de blog** para startup jurídica em Markdown.

Princípios do desenho:

| Princípio | Como funciona |
|-----------|----------------|
| Sessão legítima | Login manual pelo usuário; sem bypass de captcha ou MFA |
| CDP | Reutiliza a aba aberta no Brave (`--remote-debugging-port`) |
| Dados reais | Extração do DOM do Dino (visualizações, distribuições) |
| IA multimodal | Groq Vision analisa JSON + imagem do dashboard |
| Rastreabilidade | Log em JSONL + artefatos em `posts/` e `screenshots/` |

---

## Fluxo da pipeline

```text
scripts/start_brave_debug.bat
        │
        ▼
Login manual no Dino (dashboard)
        │
        ▼
python main.py  →  Conecta CDP  →  Extrai métricas
        │                              │
        │                              ▼
        │                      Screenshot PNG
        │                              │
        └──────────────────────────────┼──► Groq Vision
                                       │
                                       ▼
                         Post Markdown (posts/)
                         Registro (results.jsonl)
```

---

## Funcionalidades

- **Terminal interativo** (Rich + InquirerPy) com verificação de ambiente, edição de `.env` e histórico
- **CLI direta**: `python main.py --check` e `python main.py --run`
- **Extração** do resumo do dashboard Dino (`.box-resumo-trafego`)
- **Screenshot** da viewport e recorte do bloco de resumo
- **Geração de post** com título, subtítulo, corpo Markdown, tags, CTA e meta descrição
- **Pacotes de Instagram Stories** 9:16 com roteiro, PNG final, marca, CTA e página de revisão
- **Retry** com backoff exponencial em falhas transitórias

---

## Arquitetura do código

```text
zero-insight/                    # nome da pasta do repositório (pode variar)
├── main.py                      # Entrada: python main.py
├── zero_insight/
│   ├── config/                  # Settings e persistência do .env
│   ├── core/                    # async_runner (loop seguro no Cursor/VS Code)
│   ├── browser/                 # CDP + extração Dino
│   ├── capture/                 # Screenshots Playwright
│   ├── ai/                      # Groq + geração de blog jurídico
│   ├── pipeline/                # Orquestração e JSONL
│   └── cli/                     # Menu terminal e argparse
├── scripts/
│   └── start_brave_debug.bat    # Brave em modo debug (Windows)
├── screenshots/                 # Gerado (gitignore)
├── posts/                       # Posts .md gerados (gitignore)
├── stories/                     # Pacotes de Stories gerados (gitignore)
├── results.jsonl                # Histórico de execuções (gitignore)
├── .env.example
├── requirements.txt
├── LICENSE                      # Uso restrito — Requisite Legal Tech
└── README.md
```

---

## Requisitos

- Python **3.10+** (testado em 3.14)
- [Brave](https://brave.com/) instalado (Windows)
- Conta [Groq](https://console.groq.com/) com API key e modelo de **visão** habilitado
- Acesso ao dashboard Dino (`TARGET_URL` no `.env`)
- PySide6 para a interface desktop

---

## Instalação

```bash
git clone https://github.com/Konazin/automacao-posts.git   # renomeie a pasta para zero-insight, se desejar
cd automacao-posts

python -m venv .venv
.venv\Scripts\activate          # Windows

pip install -r requirements.txt
playwright install chromium
```

---

## Configuração

```bash
copy .env.example .env
```

Edite `.env` — variáveis principais:

| Variável | Descrição |
|----------|-----------|
| `CDP_PORT` | Porta debug do Brave (padrão `9222`) |
| `BRAVE_EXECUTABLE_PATH` | Caminho opcional para `brave.exe` |
| `ZEROINSIGHT_APP_DATA_DIR` | Diretório de dados da UI, padrão `%LOCALAPPDATA%\ZeroInsight` |
| `ZEROINSIGHT_OUTPUT_DIR` | Diretório base opcional para outputs |
| `ZEROINSIGHT_UI_THEME` | Tema da UI, atualmente `dark` |
| `TARGET_URL` | URL do dashboard Dino |
| `GROQ_API_KEY` | Chave da API Groq |
| `GROQ_VISION_MODEL` | Modelo com visão (ex.: `meta-llama/llama-4-scout-17b-16e-instruct`) |
| `GROQ_MODEL` | Modelo texto (usado no teste `--check`) |
| `BLOG_BRAND_NAME` | Nome da marca no post (ex.: Requisite Legal Tech) |
| `POSTS_DIR` | Pasta dos Markdown gerados |
| `SCREENSHOTS_DIR` | Pasta dos PNGs |
| `OUTPUT_FILE` | Arquivo JSONL de histórico |
| `STORIES_DIR` | Pasta dos pacotes de Stories |
| `STORY_WIDTH` / `STORY_HEIGHT` | Dimensão final dos Stories, padrão 1080x1920 |
| `STORY_DEFAULT_TEMPLATE` | Template padrão (`legal_clean`) |
| `STORY_BRAND_NAME` | Marca renderizada nos Stories |
| `STORY_BRAND_PRIMARY_COLOR` / `STORY_BRAND_SECONDARY_COLOR` | Cores do mock provider |
| `STORY_LOGO_PATH` | Reservado para logo em versão futura |
| `IMAGE_PROVIDER` | Provider de imagem, atualmente `mock` |
| `DEFAULT_BRAND_PROFILE_ID` | Marca padrão para UI/CLI |
| `DEFAULT_TEXT_PROVIDER` | Provider de texto padrão (`mock`, `custom`, `openai`, `groq`, etc.) |
| `DEFAULT_IMAGE_PROVIDER` | Provider de imagem padrão (`mock`, `custom`, `openai`, etc.) |
| `DEFAULT_VISION_PROVIDER` | Provider de visão padrão |
| `ALLOW_EXTERNAL_AI_FOR_BRAND_DOCS` | Permite envio de documentos de marca a IA externa quando `true` |
| `AI_PROVIDERS_JSON` | Configuração JSON de providers custom/OpenAI-compatible |

**Nunca** commite o arquivo `.env` (já está no `.gitignore`).

---

## Uso

### 1. Iniciar o Brave em modo debug

```bat
scripts\start_brave_debug.bat
```

- Abre o Brave com perfil isolado (`BraveAutomationDebug`)
- Navega para o dashboard Dino
- Faça login manualmente e mantenha a aba do dashboard aberta

### 2. Executar a aplicação

**Menu interativo (recomendado):**

```bash
python main.py
```

**Linha de comando:**

```bash
python main.py --check    # testa Brave CDP + Groq
python main.py --run      # pipeline completo sem menu
python main.py --ui       # abre a interface desktop
python main.py --story --topic "RPV Federal" --slides 3 --cta "Fale com a Requisite"
python main.py --story --topic "RPV Federal" --slides 3 --brand "Requisite"
python main.py --import-brand-doc "manual.pdf" --brand-name "Requisite"
python main.py --list-ai-providers
python main.py --test-ai-provider text:mock
python main.py --story --template legal_clean
python main.py --story --from-dino
python -m zero_insight   # equivalente ao menu
```

### 3. Saídas geradas

| Artefato | Conteúdo |
|----------|----------|
| `posts/YYYYMMDD_titulo.md` | Post pronto para revisão/publicação |
| `screenshots/dashboard_*.png` | Captura da tela |
| `screenshots/resumo_*.png` | Recorte do bloco de métricas |
| `results.jsonl` | JSON por linha: input, screenshot, blog_post, paths |

### 4. Interface desktop

```bash
python main.py --ui
python -m zero_insight.desktop.app
```

A UI abre em tema escuro e organiza os fluxos em Dashboard, Ambiente, Brave, Gerar Post, Gerar Stories, Saídas, Configurações e Logs.

| Tela | O que faz |
|------|-----------|
| Dashboard | Mostra status de Brave, CDP, URL, API, última execução e último output |
| Ambiente | Roda checks equivalentes ao `--check` e mostra ações recomendadas |
| Brave | Detecta `brave.exe`, instala via `winget` quando disponível, inicia Brave dedicado com CDP e abre o dashboard |
| Gerar Post | Chama a pipeline antiga de blog Markdown sem duplicar lógica |
| Gerar Stories | Chama a pipeline de Stories e gera PNGs, `manifest.json`, `story_script.json` e `review.html` |
| Saídas | Lista posts e campanhas recentes e abre a pasta de saída |
| Configurações | Salva `.env` local com URL, porta, chaves e marca |
| Logs | Mostra logs em tempo real, com botões copiar e limpar |
| Marcas | Importa PDF/DOCX, gera e edita BrandProfile, valida e define marca padrão |
| IA / Providers | Escolhe providers padrão, cadastra provider custom e testa geração curta |

O botão **Instalar Brave** tenta `winget install -e --id Brave.Brave` e depois `winget install -e --id BraveSoftware.BraveBrowser`. Se `winget` não existir ou falhar, a UI abre a página oficial `https://brave.com/download/`.

O botão **Iniciar Brave para ZeroInsight** usa perfil dedicado em `%LOCALAPPDATA%\ZeroInsight\brave-profile`:

```text
--remote-debugging-port=9222
--user-data-dir=<appdata>/ZeroInsight/brave-profile
```

O login no Dino continua manual. A UI não automatiza senha, captcha ou MFA.

### 5. Brand Intelligence

O ZeroInsight pode importar um manual de comunicação visual em PDF ou DOCX e gerar um `BrandProfile` estruturado. O fluxo local padrão não envia o documento para IA externa.

```bash
python main.py --import-brand-doc "manual.pdf"
python main.py --import-brand-doc "manual.docx" --brand-name "Requisite"
```

Saída esperada:

```text
%LOCALAPPDATA%/ZeroInsight/brands/
  requisite/
    brand_profile.json
    source/
      manual.pdf
    assets/
      extracted_image_01.png
```

Em ambiente de desenvolvimento sem permissão de escrita em `%LOCALAPPDATA%`, o app usa `.zeroinsight_appdata/` dentro do projeto, que está no `.gitignore`.

O `BrandProfile` contém nome da marca, resumo, tom de voz, termos proibidos/preferidos, paleta, regras de logo/layout/imagem, público, CTA e regras de compliance. Se nenhuma IA externa estiver configurada, a extração usa heurísticas locais e marca o perfil como `needs_review`.

### 6. IA / Providers

Providers disponíveis no MVP:

| Tipo | Providers |
|------|-----------|
| Texto | `mock`, `custom`, `openai`, `anthropic`, `gemini`, `groq` |
| Imagem | `mock`, `custom`, `openai`, `stability`, `replicate` |
| Visão | `mock`, `custom`, `openai`, `gemini`, `groq` |

O provider `custom` usa formato OpenAI-compatible no MVP. Configure por `AI_PROVIDERS_JSON` ou pela tela **IA / Providers**.

```bash
python main.py --list-ai-providers
python main.py --test-ai-provider text:mock
python main.py --test-ai-provider text:custom
```

Exemplo simplificado de `AI_PROVIDERS_JSON`:

```json
{
  "text": {
    "custom": {
      "model": "modelo",
      "base_url": "https://api.exemplo.com/v1",
      "api_key_env": "CUSTOM_AI_KEY"
    }
  }
}
```

Ao usar IA externa para documentos de marca, o conteúdo do documento poderá ser enviado ao provider configurado. Isso só deve ser habilitado com `ALLOW_EXTERNAL_AI_FOR_BRAND_DOCS=true` ou pela UI.

### 7. Gerar Instagram Stories

O comando `--story` gera um pacote para revisão humana e publicação manual. Esta entrega **não** publica automaticamente no Instagram.

```bash
python main.py --story
python main.py --story --topic "RPV Federal" --slides 3 --cta "Fale com a Requisite"
python main.py --story --topic "RPV Federal" --slides 3 --brand "Requisite"
python main.py --story --template legal_clean
python main.py --story --from-dino
```

Entradas aceitas pela CLI:

| Opção | Descrição |
|-------|-----------|
| `--topic` | Tema da campanha |
| `--objective` | Objetivo do roteiro |
| `--audience` | Público-alvo |
| `--tone` | Tom de voz |
| `--cta` | Chamada para ação |
| `--slides` | Quantidade de Stories |
| `--template` | Template visual (`legal_clean` ou `metric_card`) |
| `--from-dino` | Tenta reaproveitar métricas do dashboard Dino via CDP |
| `--brand` | Usa BrandProfile salvo para tom, cores, CTA e validação |
| `--ai-text-provider` | Provider de texto |
| `--ai-image-provider` | Provider de imagem |

Saída gerada:

```text
stories/
  YYYYMMDD_nome_da_campanha/
    manifest.json
    story_script.json
    story_01.png
    story_02.png
    story_03.png
    review.html
```

O MVP usa `IMAGE_PROVIDER=mock`, sem API externa. O provider cria uma imagem base simples em PNG 1080x1920 e o texto real é renderizado depois pelo sistema com Pillow. O `manifest.json` registra paths relativos, status do pacote e resultado da validação.

Quando uma marca é informada, o Story aplica cores e nome da marca, ajusta copy/prompt visual com o BrandProfile e grava `brand_profile_used`, `ai_providers_used` e `brand_validation` no manifest.

---

## Build Windows

O build usa PyInstaller e, se disponível, Inno Setup.

```powershell
powershell -ExecutionPolicy Bypass -File packaging\build_windows.ps1
```

O script cria `.venv-build`, instala dependências, roda `compileall`, gera `dist/ZeroInsight/ZeroInsight.exe` e compila `packaging/inno/zeroinsight.iss` quando `iscc.exe` está instalado.

O executável empacotado abre a UI por padrão. O bundle inclui templates e prompts, mas não inclui `.env`, screenshots, posts, stories ou outputs do usuário.

Para gerar instalador manualmente:

```powershell
iscc packaging\inno\zeroinsight.iss
```

---

## Menu do terminal

| Opção | Ação |
|-------|------|
| Executar pipeline | Extração → screenshot → Groq → salvar |
| Verificar conexões | Testa CDP (Brave) e API Groq |
| Ver / editar configuração | Consulta ou altera `.env` |
| Histórico | Últimos registros do JSONL |
| Ajuda | Pré-requisitos e comandos |

Se o menu com setas falhar (alguns terminais do IDE), use o **menu numérico** alternativo.

---

## Segurança e conformidade

- Não implementa bypass de captcha, MFA ou autenticação
- Credenciais apenas em variáveis de ambiente
- Sessão iniciada pelo usuário no navegador
- Dados de dashboard e posts podem conter informação operacional — tratar como **confidencial**
- Uso alinhado às políticas internas da RequisiteRPV e à LGPD
- Stories são validados contra promessas absolutas como "garantido", "100% aprovado", "sem risco" e "dinheiro imediato garantido"
- Todo pacote de Stories fica em status `AWAITING_REVIEW` antes de qualquer uso externo
- API keys não devem ser versionadas; use `.env` local ou variáveis de ambiente
- Logs não imprimem API key nem documento completo
- Documentos de marca só devem ser enviados a IA externa com autorização explícita

---

## Limitações conhecidas

- Depende da estrutura atual do DOM do Dino (classes `.box-resumo-trafego`)
- Requer Brave aberto com debug na porta configurada
- Modelo Groq Vision deve estar disponível na conta
- Mudanças na interface do Dino podem exigir ajuste em `zero_insight/browser/extract.py`
- Publicação automática no Instagram ainda não foi implementada
- O provider de imagem real ainda não existe; o MVP usa `MockImageProvider`
- Templates HTML existem como estrutura, mas a renderização final atual usa Pillow para compatibilidade Windows
- PDF escaneado sem texto não passa por OCR no MVP
- Providers Anthropic/Gemini/Stability/Replicate são adapters preparados; sem credenciais/configuração retornam erro amigável
- Provider custom aceita formato OpenAI-compatible no MVP

---

## Desenvolvimento interno

```bash
python -m py_compile main.py zero_insight/cli/main.py zero_insight/pipeline/runner.py
```

Módulos principais:

- `zero_insight.browser.extract` — métricas do dashboard
- `zero_insight.capture.screenshot` — PNGs
- `zero_insight.ai.blog` — prompt jurídico + Groq Vision
- `zero_insight.pipeline.runner` — orquestração e retries

---

## Problemas comuns

| Sintoma | Solução |
|---------|---------|
| Falha ao conectar CDP | Execute `scripts\start_brave_debug.bat` e mantenha o Brave aberto |
| Métricas zeradas / N/A | Aguarde o dashboard carregar; confira a aba correta do Dino |
| Erro no modelo Groq | Verifique `GROQ_VISION_MODEL` e permissões da chave |
| Menu não abre no IDE | Use o menu numérico ou terminal `cmd` / PowerShell externo |
| `MissingStyle` / UI | Atualize para a versão mais recente do repositório |

---

## Licença e propriedade

Software proprietário desenvolvido para a **RequisiteRPV LTDA**. Uso restrito conforme [`LICENSE`](LICENSE).

Não utilize, copie ou distribua este projeto fora do escopo autorizado pela empresa.

---

## Contato interno

Para liberação de acesso, dúvidas de compliance ou evolução do produto, contate a equipe de tecnologia / responsável pelo projeto na RequisiteRPV LTDA.
