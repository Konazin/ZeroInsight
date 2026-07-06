import type { ReactNode } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  type TextInputProps,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { colors, font, radius, spacing } from "../theme";

// ── Screen container ────────────────────────────────────────────────────────

export function Screen({ children, scroll = true }: { children: ReactNode; scroll?: boolean }) {
  return (
    <SafeAreaView style={styles.screen} edges={["top", "left", "right"]}>
      {scroll ? (
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {children}
        </ScrollView>
      ) : (
        <View style={styles.scrollContent}>{children}</View>
      )}
    </SafeAreaView>
  );
}

// ── Headings ────────────────────────────────────────────────────────────────

export function PageTitle({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <View style={{ marginBottom: spacing.lg }}>
      <Text style={styles.pageTitle}>{title}</Text>
      {subtitle ? <Text style={styles.pageSubtitle}>{subtitle}</Text> : null}
    </View>
  );
}

// ── Card ────────────────────────────────────────────────────────────────────

export function Card({ children, style }: { children: ReactNode; style?: object }) {
  return <View style={[styles.card, style]}>{children}</View>;
}

// ── Button ──────────────────────────────────────────────────────────────────

export function Button({
  label,
  onPress,
  variant = "primary",
  loading = false,
  disabled = false,
  icon,
}: {
  label: string;
  onPress: () => void;
  variant?: "primary" | "ghost" | "danger";
  loading?: boolean;
  disabled?: boolean;
  icon?: ReactNode;
}) {
  const isDisabled = disabled || loading;
  const bg =
    variant === "primary" ? colors.accent : variant === "danger" ? colors.danger : "transparent";
  const borderColor = variant === "ghost" ? colors.border : "transparent";
  const textColor = variant === "ghost" ? colors.textMuted : "#fff";

  return (
    <Pressable
      onPress={onPress}
      disabled={isDisabled}
      style={({ pressed }) => [
        styles.button,
        { backgroundColor: bg, borderColor, opacity: isDisabled ? 0.4 : pressed ? 0.85 : 1 },
      ]}
    >
      {loading ? (
        <ActivityIndicator color={textColor} size="small" />
      ) : (
        <>
          {icon}
          <Text style={[styles.buttonText, { color: textColor }]}>{label}</Text>
        </>
      )}
    </Pressable>
  );
}

// ── Field / input ───────────────────────────────────────────────────────────

export function Field({
  label,
  hint,
  ...inputProps
}: { label: string; hint?: string } & TextInputProps) {
  return (
    <View style={{ marginBottom: spacing.md }}>
      <Text style={styles.fieldLabel}>{label}</Text>
      <TextInput
        placeholderTextColor={colors.textSubtle}
        style={styles.input}
        {...inputProps}
      />
      {hint ? <Text style={styles.fieldHint}>{hint}</Text> : null}
    </View>
  );
}

// ── Feedback banner ─────────────────────────────────────────────────────────

export function Banner({ kind, children }: { kind: "info" | "success" | "error" | "warning"; children: ReactNode }) {
  const map = {
    info: { color: colors.accentLight, bg: "rgba(124,58,237,0.10)" },
    success: { color: colors.success, bg: "rgba(34,197,94,0.10)" },
    error: { color: colors.danger, bg: "rgba(239,68,68,0.10)" },
    warning: { color: colors.warning, bg: "rgba(245,158,11,0.10)" },
  }[kind];
  return (
    <View style={[styles.banner, { backgroundColor: map.bg, borderColor: map.color }]}>
      <Text style={{ color: map.color, fontSize: font.small, fontWeight: "500" }}>{children}</Text>
    </View>
  );
}

// ── Pill / tag ──────────────────────────────────────────────────────────────

export function Pill({ label, active = false }: { label: string; active?: boolean }) {
  return (
    <View
      style={[
        styles.pill,
        {
          backgroundColor: active ? colors.accentBg : colors.bgElevated,
          borderColor: active ? colors.accent : colors.border,
        },
      ]}
    >
      <Text style={{ color: active ? colors.accentLight : colors.textMuted, fontSize: font.small }}>
        {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bgBase },
  scrollContent: { padding: spacing.lg, paddingBottom: spacing.xl * 2 },
  pageTitle: { color: colors.textPrimary, fontSize: font.h1, fontWeight: "700", letterSpacing: -0.4 },
  pageSubtitle: { color: colors.textMuted, fontSize: font.body, marginTop: 4, lineHeight: 20 },
  card: {
    backgroundColor: colors.bgSurface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: radius.lg,
    padding: spacing.lg,
    marginBottom: spacing.md,
  },
  button: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    borderWidth: 1,
    borderRadius: radius.sm,
    paddingVertical: 13,
    paddingHorizontal: spacing.lg,
  },
  buttonText: { fontSize: font.body, fontWeight: "600" },
  fieldLabel: {
    color: colors.textSubtle,
    fontSize: font.tiny,
    fontWeight: "700",
    textTransform: "uppercase",
    letterSpacing: 0.6,
    marginBottom: 6,
  },
  fieldHint: { color: colors.textSubtle, fontSize: font.tiny, marginTop: 4 },
  input: {
    backgroundColor: colors.bgInput,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.md,
    paddingVertical: 11,
    color: colors.textPrimary,
    fontSize: font.body,
  },
  banner: {
    borderWidth: 1,
    borderRadius: radius.sm,
    padding: spacing.md,
    marginTop: spacing.sm,
  },
  pill: {
    borderWidth: 1,
    borderRadius: radius.pill,
    paddingVertical: 4,
    paddingHorizontal: 12,
  },
});
