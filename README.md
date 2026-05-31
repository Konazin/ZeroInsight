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
| `TARGET_URL` | URL do dashboard Dino |
| `GROQ_API_KEY` | Chave da API Groq |
| `GROQ_VISION_MODEL` | Modelo com visão (ex.: `meta-llama/llama-4-scout-17b-16e-instruct`) |
| `GROQ_MODEL` | Modelo texto (usado no teste `--check`) |
| `BLOG_BRAND_NAME` | Nome da marca no post (ex.: Requisite Legal Tech) |
| `POSTS_DIR` | Pasta dos Markdown gerados |
| `SCREENSHOTS_DIR` | Pasta dos PNGs |
| `OUTPUT_FILE` | Arquivo JSONL de histórico |

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
python -m zero_insight   # equivalente ao menu
```

### 3. Saídas geradas

| Artefato | Conteúdo |
|----------|----------|
| `posts/YYYYMMDD_titulo.md` | Post pronto para revisão/publicação |
| `screenshots/dashboard_*.png` | Captura da tela |
| `screenshots/resumo_*.png` | Recorte do bloco de métricas |
| `results.jsonl` | JSON por linha: input, screenshot, blog_post, paths |

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
- Uso alinhado às políticas internas da Requisite Legal Tech e à LGPD

---

## Limitações conhecidas

- Depende da estrutura atual do DOM do Dino (classes `.box-resumo-trafego`)
- Requer Brave aberto com debug na porta configurada
- Modelo Groq Vision deve estar disponível na conta
- Mudanças na interface do Dino podem exigir ajuste em `zero_insight/browser/extract.py`

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

Software proprietário desenvolvido para a **Requisite Legal Tech**. Uso restrito conforme [`LICENSE`](LICENSE).

Não utilize, copie ou distribua este projeto fora do escopo autorizado pela empresa.

---

## Contato interno

Para liberação de acesso, dúvidas de compliance ou evolução do produto, contate a equipe de tecnologia / responsável pelo projeto na Requisite Legal Tech.
