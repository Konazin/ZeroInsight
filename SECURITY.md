# Política de Segurança — ZeroInsight

## Modelo de ameaça

O ZeroInsight roda **localmente** na máquina do usuário: um backend FastAPI em
`127.0.0.1:8765` que serve o frontend React e chama APIs de IA (OpenAI, Groq).
As chaves de API ficam em `.env` local. As principais superfícies de risco são:

1. **Leitura arbitrária de arquivos** — o backend serve arquivos gerados por
   caminho. Sem contenção, isso permitiria ler `.env` (chaves de API) ou
   arquivos do sistema.
2. **Vazamento de informação** — mensagens de erro internas expostas ao cliente.
3. **Exposição na rede** — se o backend for exposto além de `localhost`,
   qualquer um na rede poderia acionar gerações (custo de API) ou ler saídas.

## Mitigações implementadas

| Área | Mitigação |
|------|-----------|
| Path traversal / LFI | `zero_insight/server/security.py::safe_output_path` contém todo acesso a arquivo às raízes de saída (`stories/`, `posts/`, `screenshots/`) e assets de marca. Caminhos absolutos do sistema e `../` são rejeitados (403). |
| Identificadores em caminho | `validate_identifier` rejeita separadores e `..` em `brand_id`. |
| Vazamento de erros | Respostas 500 retornam mensagem genérica; o stack trace vai só para os logs do servidor. |
| Tamanho de payload | Middleware rejeita requisições acima de 20 MB; arquivos servidos limitados a 25 MB. |
| Validação de entrada | Schemas Pydantic com `max_length` e limites numéricos em todos os campos de geração. |
| Headers HTTP | `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`. |
| CORS | Origens restritas a `localhost`/`127.0.0.1` (portas do Vite) + `frontend_url` configurado. Métodos e headers explícitos. |
| Documentação da API | `/api/docs`, `/api/redoc` e OpenAPI desabilitados no app empacotado (`sys.frozen`). |
| Segredos em log | Chaves de API nunca são logadas; a UI só recebe versões mascaradas (`sk-...abcd`). |

## Chaves de API

- Ficam **apenas** em `.env` local (no `.gitignore`) — nunca versionadas.
- A API `GET /api/settings` retorna as chaves mascaradas (`****`).
- No app **mobile** (`mobile/`), a chave é guardada com `expo-secure-store`
  (Keychain no iOS / Keystore no Android), nunca em `AsyncStorage` em texto puro.

> **Nota sobre o app mobile standalone:** ele chama a OpenAI diretamente do
> dispositivo, então a chave de API reside no aparelho. Isso é aceitável para
> uso pessoal, mas **não** distribua um build com a chave embutida. Cada usuário
> deve inserir a própria chave, guardada no armazenamento seguro do SO.

## Exposição na rede (não recomendado)

O backend foi projetado para `127.0.0.1`. Se você **precisar** expô-lo na rede,
adicione autenticação por token e rate-limiting antes — não há autenticação por
padrão porque o modelo é single-user local.

## Reportar uma vulnerabilidade

Envie um e-mail para **m4caun4@gmail.com** com passos de reprodução.
Não abra issues públicas para falhas de segurança.
