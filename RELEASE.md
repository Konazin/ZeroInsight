## Release — ZeroInsight v2.0

**Versão do instalador:** `2.0.0`
**Arquivo:** `ZeroInsight Setup 2.0.0.exe`
**Plataforma:** Windows 10/11 x64

---

### O que há de novo

**ZeroInsight agora é um app Windows nativo**, sem precisar instalar Python, Node.js ou abrir terminal. Funciona como Discord ou Spotify — abre com um ícone na área de trabalho, carrega num segundo e fecha tudo quando você fecha a janela.

**Novas funcionalidades (v2.0):**
- Interface redesenhada com tema **Midnight Purple** — visual mais escuro, premium e focado
- Dashboard simplificado com CTA direto para geração de stories
- Formulário de briefing reorganizado em seções visuais (tema, visual, contexto)
- Geração de stories em lote com progresso em tempo real
- Logo da marca embutida nas imagens via API OpenAI
- Modo de prompt manual para usuários avançados
- **Instalador nativo Windows** (NSIS) — instala em 30 segundos, cria atalho no desktop

---

### Como instalar

1. Baixe `ZeroInsight Setup 2.0.0.exe`
2. Execute e clique em *Instalar*
3. Abra pelo atalho criado no desktop
4. Na primeira vez, vá em **Configurações** e insira sua chave de API OpenAI

---

### Notas técnicas

- Backend Python 3.12 + FastAPI embutido (sem dependência externa de Python)
- Frontend React 19 servido diretamente pelo backend
- Dados gerados salvos em `~/Documents/ZeroInsight/`
- Configurações em `OPENAI_API_KEY` via tela de configurações do app
