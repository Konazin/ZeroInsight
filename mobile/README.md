# ZeroInsight Mobile

App **React Native (Expo managed)** para gerar Instagram Stories com IA direto do
celular. Standalone: chama a OpenAI diretamente do dispositivo, sem depender do
backend Python do ZeroInsight desktop.

## Stack

| Camada | Tecnologia |
|--------|------------|
| Runtime | Expo SDK 51 · React Native 0.74 · React 18 |
| Navegação | React Navigation (bottom tabs) |
| Segurança | expo-secure-store (Keychain/Keystore) para a chave de API |
| Arquivos | expo-file-system (imagens salvas no dispositivo) |
| IA | OpenAI (`/chat/completions` para roteiro, `/images/generations` para imagem) |
| Ícones | lucide-react-native |

## Rodando

```bash
cd mobile
npm install
npm start          # abre o Expo Dev Tools; use o Expo Go para testar no celular
# ou
npm run android
npm run ios
```

Na primeira execução, vá em **Config** e insira sua chave OpenAI (`sk-...`).
A chave é guardada no cofre seguro do sistema — nunca em texto puro.

## Estrutura

```
mobile/
├── App.tsx                     # entry: providers + navegação
├── index.ts                    # registerRootComponent
├── app.json                    # config Expo (tema dark, bundle ids)
└── src/
    ├── theme.ts                # paleta Midnight Purple (espelha o desktop)
    ├── components/ui.tsx        # Screen, Card, Button, Field, Banner, Pill
    ├── context/ConfigContext.tsx  # chave/modelos carregados do SecureStore
    ├── lib/
    │   ├── secureStore.ts      # armazenamento seguro da chave
    │   ├── openai.ts           # cliente OpenAI standalone (fetch)
    │   └── storyPipeline.ts    # roteiro → imagens → salva no device
    ├── navigation/             # bottom tabs
    └── screens/
        ├── DashboardScreen.tsx
        ├── GenerateStoryScreen.tsx
        ├── SettingsScreen.tsx
        └── OutputsScreen.tsx
```

## Segurança

- A chave OpenAI fica **apenas** no dispositivo, via `expo-secure-store`.
- **Não** publique um build com a chave embutida — cada usuário insere a sua.
- Nenhum dado passa por servidores da Requisite; o app fala direto com a OpenAI.

Veja [`../SECURITY.md`](../SECURITY.md) para a política completa.

## Próximos passos

- Perfis de marca (BrandProfile) e injeção de logo via `/images/edit`
- Compartilhamento nativo das imagens (expo-sharing)
- Salvar no rolo da câmera (expo-media-library)
