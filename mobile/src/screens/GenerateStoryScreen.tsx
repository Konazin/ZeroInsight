import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { Sparkles } from "lucide-react-native";
import { useState } from "react";
import { Image, StyleSheet, Text, View } from "react-native";
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
        <Field label="Tema principal *" value={topic} onChangeText={setTopic} placeholder="Ex: RPV Federal" />
        <Field label="Objetivo" value={objective} onChangeText={setObjective} />
        <Field label="Público-alvo" value={audience} onChangeText={setAudience} />
        <Field label="Tom de voz" value={tone} onChangeText={setTone} />
        <Field label="CTA" value={cta} onChangeText={setCta} />
        <Field
          label="Número de slides (1–10)"
          value={slidesText}
          onChangeText={setSlidesText}
          keyboardType="number-pad"
          hint={`Serão gerados ${slides} slide(s).`}
        />
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
          icon={<Sparkles size={17} color="#fff" />}
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
  progressStep: { color: colors.textPrimary, fontSize: font.body, fontWeight: "600", marginBottom: spacing.sm },
  progressTrack: {
    height: 6,
    borderRadius: radius.pill,
    backgroundColor: colors.bgElevated,
    overflow: "hidden",
  },
  progressFill: { height: 6, borderRadius: radius.pill, backgroundColor: colors.accent },
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
