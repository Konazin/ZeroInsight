## Release — ZeroInsight v2.0.2

**Versão do instalador:** `2.0.2`
**Plataforma:** Windows 10/11 x64 · App mobile: Android/iOS (Expo)

---

### Segurança e robustez (v2.0.2)

- **Correção crítica — leitura arbitrária de arquivos:** a rota `/api/outputs/file`
  aceitava qualquer caminho, permitindo ler `.env` (chaves de API) e arquivos do
  sistema. Agora todo acesso é contido às pastas de saída (`stories/`, `posts/`,
  `screenshots/`); caminhos externos retornam 403.
- Respostas de erro 500 deixaram de vazar detalhes internos (stack traces).
- Validação de entrada (Pydantic com limites), headers de segurança HTTP, limite
  de tamanho de requisição e documentação da API desabilitada no app empacotado.
- `httpx.get` de download de imagem agora tem timeout explícito (não trava mais).
- Novo `SECURITY.md` e workflow de CI de segurança (bandit + pip-audit + npm audit).

### Novo — App mobile (React Native / Expo)

- App standalone que gera Stories com IA direto do celular, chamando a OpenAI.
- Chave de API guardada no cofre seguro do dispositivo (Keychain/Keystore).
- Veja [`mobile/README.md`](mobile/README.md).

---

## Release — ZeroInsight v2.0.1

**Versão do instalador:** `2.0.1`
**Arquivo:** `ZeroInsight Setup 2.0.1.exe`
**Plataforma:** Windows 10/11 x64

---

### Correções (v2.0.1)

- **`start.bat` reescrito**: cria o `.venv` automaticamente, instala dependências Python antes de iniciar — elimina o erro `ModuleNotFoundError: No module named 'fastapi'` ao rodar da fonte
- **Aviso de Node.js ausente**: exibe instruções com `winget install OpenJS.NodeJS.LTS` quando `npm` não é encontrado
- **`build-app.ps1` com validações**: verifica pré-requisitos (Python, Node.js), instala `requirements.txt` antes do PyInstaller, valida que `backend.exe` foi gerado e que o instalador `.exe` foi criado — impede que um build quebrado chegue ao usuário
- **`PySide6` excluído do bundle PyInstaller**: estava listado em `requirements.txt` mas não é usado pelo servidor FastAPI; excluir reduz o tamanho do bundle e elimina conflitos de Qt em tempo de build
- **Versão corrigida**: `package.json` estava em `0.2.0`; corrigido para `2.0.1` para que o instalador gerado pelo `electron-builder` tenha o nome correto

---

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
