import { useNavigation } from "@react-navigation/native";
import type { NativeStackNavigationProp } from "@react-navigation/native-stack";
import { AlertTriangle, ArrowRight, FolderOpen, Image as ImageIcon, Settings as SettingsIcon } from "lucide-react-native";
import type { ReactNode } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { Button, Card, PageTitle, Screen } from "../components/ui";
import { useConfig } from "../context/ConfigContext";
import type { RootStackParamList } from "../navigation/types";
import { colors, font, radius, spacing } from "../theme";

type Nav = NativeStackNavigationProp<RootStackParamList>;

export function DashboardScreen() {
  const navigation = useNavigation<Nav>();
  const { hasKey } = useConfig();

  return (
    <Screen>
      <PageTitle title="ZeroInsight" subtitle="Gere Stories de Instagram com IA, direto do celular." />

      {!hasKey && (
        <Pressable onPress={() => navigation.navigate("Settings")} style={styles.setupBanner}>
          <View style={styles.setupIcon}>
            <AlertTriangle size={16} color={colors.warning} />
          </View>
          <View style={{ flex: 1 }}>
            <Text style={styles.setupTitle}>Configure sua chave OpenAI</Text>
            <Text style={styles.setupDesc}>Necessária para gerar roteiros e imagens.</Text>
          </View>
          <ArrowRight size={16} color={colors.warning} />
        </Pressable>
      )}

      <Card style={styles.hero}>
        <View style={styles.heroIcon}>
          <ImageIcon size={24} color={colors.bgBase} />
        </View>
        <Text style={styles.heroTitle}>Criar novo Story</Text>
        <Text style={styles.heroDesc}>
          Descreva o tema e receba um pacote de slides com imagens prontas para postar.
        </Text>
        <Button
          label="Criar agora"
          onPress={() => navigation.navigate("Generate")}
          icon={<ArrowRight size={16} color={colors.bgBase} />}
        />
      </Card>

      <View style={{ gap: spacing.md }}>
        <ActionRow
          icon={<FolderOpen size={18} color={colors.accentLight} />}
          label="Ver Saídas"
          desc="Stories gerados anteriormente no dispositivo"
          onPress={() => navigation.navigate("Outputs")}
        />
        <ActionRow
          icon={<SettingsIcon size={18} color={colors.accentLight} />}
          label="Configurações"
          desc="Chave de API e modelos de IA"
          onPress={() => navigation.navigate("Settings")}
        />
      </View>
    </Screen>
  );
}

function ActionRow({
  icon,
  label,
  desc,
  onPress,
}: {
  icon: ReactNode;
  label: string;
  desc: string;
  onPress: () => void;
}) {
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [styles.actionRow, pressed && { opacity: 0.85 }]}>
      <View style={styles.actionIcon}>{icon}</View>
      <View style={{ flex: 1 }}>
        <Text style={styles.actionLabel}>{label}</Text>
        <Text style={styles.actionDesc}>{desc}</Text>
      </View>
      <ArrowRight size={16} color={colors.textSubtle} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  setupBanner: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    padding: spacing.md,
    marginBottom: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.bgElevated,
  },
  setupIcon: {
    width: 34,
    height: 34,
    borderRadius: 9,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.bgSurface,
  },
  setupTitle: { color: colors.textPrimary, fontSize: font.body, fontWeight: "600" },
  setupDesc: { color: colors.textSubtle, fontSize: font.small },
  hero: { alignItems: "flex-start", gap: spacing.sm },
  heroIcon: {
    width: 50,
    height: 50,
    borderRadius: 13,
    backgroundColor: colors.accent,
    alignItems: "center",
    justifyContent: "center",
    marginBottom: spacing.xs,
  },
  heroTitle: { color: colors.textPrimary, fontSize: font.h2, fontWeight: "700" },
  heroDesc: { color: colors.textMuted, fontSize: font.body, lineHeight: 20, marginBottom: spacing.sm },
  actionRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    padding: spacing.md,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.bgElevated,
  },
  actionIcon: {
    width: 40,
    height: 40,
    borderRadius: radius.md,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.accentBg,
    borderWidth: 1,
    borderColor: colors.border,
  },
  actionLabel: { color: colors.textPrimary, fontSize: font.body, fontWeight: "600" },
  actionDesc: { color: colors.textSubtle, fontSize: font.small },
});
