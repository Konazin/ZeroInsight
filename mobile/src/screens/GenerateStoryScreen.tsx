import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { Sparkles } from "lucide-react-native";
import { useState } from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { Banner, Button, Card, Field, PageTitle, Screen } from "../components/ui";
import { useConfig } from "../context/ConfigContext";
import { OpenAIError, type StoryBrief } from "../lib/openai";
import { runStoryPipeline, type ProgressUpdate, type StoryResult } from "../lib/storyPipeline";
import type { RootStackParamList } from "../navigation/types";
import { colors, font, radius, spacing } from "../theme";

type Nav = NativeStackNavigationProp<RootStackParamList>;

export function GenerateStoryScreen() {
  const navigation = useNavigation<Nav>();
  const { config, hasKey } = useConfig();

  const [topic, setTopic] = useState("RPV Federal");
  const [objective, setObjective] = useState("orientar com clareza");
  const [audience, setAudience] = useState("público jurídico");
  const [tone, setTone] = useState("claro e responsável");
  const [cta, setCta] = useState("Fale com a Requisite");
  const [slidesText, setSlidesText] = useState("3");

  const [running, setRunning] = useState(false);
  const [progress, setProgress] = useState<ProgressUpdate | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<StoryResult | null>(null);

  const slides = Math.max(1, Math.min(10, Number.parseInt(slidesText, 10) || 3));

  async function handleGenerate() {
    setError(null);
    setResult(null);
    if (!hasKey) {
      setError("Configure sua chave OpenAI em Configurações antes de gerar.");
      return;
    }
    if (!topic.trim()) {
      setError("Informe o tema principal.");
      return;
    }

    const brief: StoryBrief = {
      topic: topic.trim(),
      objective,
      audience,
      tone,
      cta,
      slides,
    };

    setRunning(true);
    try {
      const res = await runStoryPipeline(config, brief, setProgress);
      setResult(res);
    } catch (err) {
      setError(err instanceof OpenAIError ? err.message : "Falha ao gerar o story. Tente novamente.");
    } finally {
      setRunning(false);
      setProgress(null);
    }
  }

  return (
    <Screen>
      <PageTitle title="Gerar Story" subtitle="Preencha o briefing e a IA cria os slides." />

      <Card>
        <Text style={styles.sectionLabel}>CONTEÚDO</Text>
        <Field label="Tema principal *" value={topic} onChangeText={setTopic} placeholder="Ex: RPV Federal" />
        <Field label="Objetivo" value={objective} onChangeText={setObjective} />
        <Field label="Público-alvo" value={audience} onChangeText={setAudience} />
        <Text style={styles.sectionLabel}>TOM E CONVERSÃO</Text>
        <Field label="Tom de voz" value={tone} onChangeText={setTone} />
        <Field label="CTA" value={cta} onChangeText={setCta} />
        <Text style={styles.pickerLabel}>NÚMERO DE SLIDES</Text>
        <View style={styles.slidePicker}>
          {[1, 3, 5, 7, 10].map((value) => {
            const active = slides === value;
            return (
              <Pressable
                key={value}
                accessibilityRole="button"
                accessibilityState={{ selected: active }}
                onPress={() => setSlidesText(String(value))}
                style={[styles.slideOption, active && styles.slideOptionActive]}
              >
                <Text style={[styles.slideOptionText, active && styles.slideOptionTextActive]}>{value}</Text>
              </Pressable>
            );
          })}
        </View>
        <Text style={styles.pickerHint}>Cada slide gera uma imagem e consome créditos da API.</Text>
      </Card>

      {error && <Banner kind="error">{error}</Banner>}

      {running && progress && (
        <Card>
          <Text style={styles.progressStep}>{progress.step}</Text>
          <View style={styles.progressTrack}>
            <View
              style={[
                styles.progressFill,
                { width: `${Math.round((progress.current / progress.total) * 100)}%` as `${number}%` },
              ]}
            />
          </View>
          <Text style={styles.progressHint}>
            Etapa {progress.current} de {progress.total} · não feche o app.
          </Text>
        </Card>
      )}

      {!result && (
        <Button
          label={running ? "Gerando…" : "Gerar stories agora"}
          onPress={handleGenerate}
          loading={running}
          icon={<Sparkles size={17} color={colors.bgBase} />}
        />
      )}

      {result && (
        <Card>
          <Banner kind="success">Pacote gerado com {result.slides.length} slide(s)!</Banner>
          <View style={styles.thumbRow}>
            {result.slides.map((s) => (
              <Image key={s.imageUri} source={{ uri: s.imageUri }} style={styles.thumb} />
            ))}
          </View>
          <View style={{ gap: spacing.sm, marginTop: spacing.sm }}>
            <Button label="Ver nas Saídas" onPress={() => navigation.navigate("Outputs")} />
            <Button
              label="Gerar outro"
              variant="ghost"
              onPress={() => {
                setResult(null);
                setError(null);
              }}
            />
          </View>
        </Card>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  sectionLabel: {
    color: colors.textPrimary,
    fontSize: font.tiny,
    fontWeight: "800",
    letterSpacing: 1.1,
    marginBottom: spacing.md,
    marginTop: spacing.xs,
  },
  pickerLabel: {
    color: colors.textSubtle,
    fontSize: font.tiny,
    fontWeight: "700",
    letterSpacing: 0.6,
    marginBottom: spacing.sm,
  },
  slidePicker: { flexDirection: "row", gap: spacing.sm },
  slideOption: {
    flex: 1,
    minHeight: 44,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.bgInput,
    alignItems: "center",
    justifyContent: "center",
  },
  slideOptionActive: { backgroundColor: colors.textPrimary, borderColor: colors.textPrimary },
  slideOptionText: { color: colors.textMuted, fontSize: font.body, fontWeight: "700" },
  slideOptionTextActive: { color: colors.bgBase },
  pickerHint: { color: colors.textSubtle, fontSize: font.tiny, marginTop: spacing.sm },
  progressStep: { color: colors.textPrimary, fontSize: font.body, fontWeight: "600", marginBottom: spacing.sm },
  progressTrack: {
    height: 6,
    borderRadius: radius.pill,
    backgroundColor: colors.bgElevated,
    overflow: "hidden",
  },
  progressFill: { height: 6, borderRadius: radius.pill, backgroundColor: colors.textPrimary },
  progressHint: { color: colors.textSubtle, fontSize: font.tiny, marginTop: spacing.sm },
  thumbRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm, marginTop: spacing.md },
  thumb: {
    width: 72,
    height: 128,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.bgElevated,
  },
});
