import { ShieldCheck } from "lucide-react-native";
import { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { Banner, Button, Card, Field, PageTitle, Screen } from "../components/ui";
import { useConfig } from "../context/ConfigContext";
import { validateKey } from "../lib/openai";
import { DEFAULT_IMAGE_MODEL, DEFAULT_TEXT_MODEL, maskKey } from "../lib/secureStore";
import { colors, font, spacing } from "../theme";

export function SettingsScreen() {
  const { config, update, reload } = useConfig();

  const [apiKey, setApiKey] = useState("");
  const [textModel, setTextModel] = useState(config.textModel || DEFAULT_TEXT_MODEL);
  const [imageModel, setImageModel] = useState(config.imageModel || DEFAULT_IMAGE_MODEL);
  const [feedback, setFeedback] = useState<{ kind: "success" | "error" | "info"; text: string } | null>(null);
  const [checking, setChecking] = useState(false);

  useEffect(() => {
    setTextModel(config.textModel || DEFAULT_TEXT_MODEL);
    setImageModel(config.imageModel || DEFAULT_IMAGE_MODEL);
  }, [config.textModel, config.imageModel]);

  async function handleSave() {
    setFeedback(null);
    const key = apiKey.trim() || config.apiKey; // mantém a chave atual se não digitou nova
    await update({ apiKey: key, textModel, imageModel });
    setApiKey("");
    setFeedback({ kind: "success", text: "Configurações salvas com segurança." });
  }

  async function handleValidate() {
    const key = apiKey.trim() || config.apiKey;
    if (!key) {
      setFeedback({ kind: "error", text: "Insira uma chave primeiro." });
      return;
    }
    setChecking(true);
    setFeedback({ kind: "info", text: "Validando chave com a OpenAI…" });
    const ok = await validateKey(key);
    setChecking(false);
    setFeedback(
      ok
        ? { kind: "success", text: "Chave válida e funcionando." }
        : { kind: "error", text: "Chave inválida ou sem acesso." },
    );
  }

  return (
    <Screen>
      <PageTitle title="Configurações" subtitle="Sua chave fica guardada no cofre seguro do dispositivo." />

      <Card>
        <View style={styles.currentKeyRow}>
          <Text style={styles.currentKeyLabel}>Chave atual</Text>
          <Text style={styles.currentKeyValue}>{maskKey(config.apiKey)}</Text>
        </View>

        <Field
          label="Chave OpenAI"
          value={apiKey}
          onChangeText={setApiKey}
          placeholder={config.apiKey ? "•••• (deixe em branco p/ manter)" : "sk-..."}
          autoCapitalize="none"
          autoCorrect={false}
          secureTextEntry
          hint="Começa com sk-. Nunca é enviada a ninguém além da OpenAI."
        />
        <Field label="Modelo de texto" value={textModel} onChangeText={setTextModel} autoCapitalize="none" />
        <Field label="Modelo de imagem" value={imageModel} onChangeText={setImageModel} autoCapitalize="none" />

        {feedback && <Banner kind={feedback.kind}>{feedback.text}</Banner>}

        <View style={{ gap: spacing.sm, marginTop: spacing.sm }}>
          <Button label="Salvar" onPress={handleSave} />
          <Button label={checking ? "Validando…" : "Testar chave"} variant="ghost" onPress={handleValidate} loading={checking} />
        </View>
      </Card>

      <Card style={styles.securityCard}>
        <View style={styles.securityHeader}>
          <ShieldCheck size={16} color={colors.success} />
          <Text style={styles.securityTitle}>Armazenamento seguro</Text>
        </View>
        <Text style={styles.securityText}>
          A chave é guardada com Keychain (iOS) / Keystore (Android) via expo-secure-store — nunca em texto puro.
          Este app fala diretamente com a OpenAI; nenhum dado passa por servidores da Requisite.
        </Text>
      </Card>

      <Button label="Recarregar configurações" variant="ghost" onPress={() => void reload()} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  currentKeyRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingBottom: spacing.md,
    marginBottom: spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: colors.borderSubtle,
  },
  currentKeyLabel: { color: colors.textSubtle, fontSize: font.small, fontWeight: "600" },
  currentKeyValue: { color: colors.textPrimary, fontSize: font.body, fontFamily: "monospace" },
  securityCard: { backgroundColor: colors.bgElevated },
  securityHeader: { flexDirection: "row", alignItems: "center", gap: spacing.sm, marginBottom: spacing.sm },
  securityTitle: { color: colors.textPrimary, fontSize: font.h3, fontWeight: "600" },
  securityText: { color: colors.textMuted, fontSize: font.small, lineHeight: 19 },
});
