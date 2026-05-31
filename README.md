# Automação Posts

Pipeline em Python que conecta ao **Brave** (sessão já logada), extrai métricas do dashboard **Dino**, captura **screenshot**, envia tudo para a **Groq Vision** e gera um **post de blog** para startup jurídica em Markdown.

## Fluxo

```
Brave (CDP) → extração DOM → screenshot PNG → Groq Vision → post Markdown + JSONL
```

## Arquitetura

```
automacao-posts/
├── main.py                      # entrada: python main.py
├── automacao_posts/
│   ├── config/                  # Settings e .env
│   ├── core/                    # async_runner, tipos
│   ├── browser/                 # CDP + extração Dino
│   ├── capture/                 # screenshots
│   ├── ai/                      # Groq + geração de blog
│   ├── pipeline/                # orquestração e JSONL
│   └── cli/                     # terminal Rich + argparse
├── scripts/
│   └── start_brave_debug.bat    # Brave em modo debug (Windows)
├── screenshots/                 # gerado (gitignore)
├── posts/                       # gerado (gitignore)
└── results.jsonl                # log de execuções (gitignore)
```

## Requisitos

- Python 3.10+
- [Brave](https://brave.com/) instalado
- Conta [Groq](https://console.groq.com/) com API key e modelo de visão habilitado

## Instalação

```bash
git clone https://github.com/SEU_USUARIO/automacao-posts.git
cd automacao-posts
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
playwright install chromium
```

## Configuração

```bash
copy .env.example .env
```

Edite `.env` e defina pelo menos `GROQ_API_KEY`. Ajuste `BLOG_BRAND_NAME` com o nome da sua startup jurídica.

| Variável | Descrição |
|----------|-----------|
| `CDP_PORT` | Porta do debug remoto do Brave (padrão `9222`) |
| `TARGET_URL` | URL do dashboard Dino |
| `GROQ_API_KEY` | Chave da API Groq |
| `GROQ_VISION_MODEL` | Modelo com visão (ex.: `meta-llama/llama-4-scout-17b-16e-instruct`) |
| `BLOG_BRAND_NAME` | Nome exibido no post gerado |
| `POSTS_DIR` | Pasta dos posts `.md` |
| `SCREENSHOTS_DIR` | Pasta dos PNGs |

## Uso

### 1. Abrir o Brave em modo debug

Duplo clique ou no terminal:

```bat
scripts\start_brave_debug.bat
```

Faça login no Dino e deixe o dashboard aberto. O script usa um perfil separado (`BraveAutomationDebug`) para não interferir no Brave do dia a dia.

### 2. Executar

**Menu interativo (recomendado):**

```bash
python main.py
```

**Linha de comando:**

```bash
python main.py --check    # testa CDP + Groq
python main.py --run        # pipeline completo sem menu
python -m automacao_posts # equivalente
```

### 3. Resultados

- `posts/YYYYMMDD_titulo.md` — post pronto para publicar
- `screenshots/dashboard_*.png` — captura da tela
- `results.jsonl` — histórico com métricas, paths e JSON do post

## Menu do terminal

| Opção | Ação |
|-------|------|
| Executar pipeline | Extração + screenshot + IA + salvar |
| Verificar conexões | Testa Brave CDP e Groq |
| Editar configuração | Altera `.env` sem editor |
| Histórico | Últimos registros do JSONL |

## Desenvolvimento

```bash
python -m py_compile automacao_posts/**/*.py  # verificar sintaxe
```

Módulos principais:

- `automacao_posts.browser.extract` — métricas do DOM Dino
- `automacao_posts.capture.screenshot` — PNG viewport + recorte
- `automacao_posts.ai.blog` — prompt jurídico + Groq Vision
- `automacao_posts.pipeline.runner` — orquestra retries e persistência

## Segurança

- **Nunca** commite `.env` (já está no `.gitignore`)
- Use `.env.example` como modelo sem segredos
- A API key Groq fica apenas na sua máquina

## Licença

MIT — use e adapte livremente.

## Problemas comuns

| Sintoma | Solução |
|---------|---------|
| Falha ao conectar CDP | Rode `scripts\start_brave_debug.bat` e mantenha o Brave aberto |
| Métricas N/A / zero | Abra o dashboard Dino na aba correta e aguarde carregar |
| Erro 404 no modelo | Troque `GROQ_VISION_MODEL` no `.env` por um modelo vision ativo na Groq |
| `asyncio.run()` no Cursor | Já tratado via `core/async_runner.py` |
