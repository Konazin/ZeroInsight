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
  const textColor = variant === "ghost" ? colors.textMuted : colors.bgBase;

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
    info: { color: colors.textPrimary, bg: colors.bgElevated },
    success: { color: colors.textPrimary, bg: colors.bgElevated },
    error: { color: colors.textPrimary, bg: colors.bgElevated },
    warning: { color: colors.textMuted, bg: colors.bgElevated },
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
          backgroundColor: active ? colors.textPrimary : colors.bgElevated,
          borderColor: active ? colors.textPrimary : colors.border,
        },
      ]}
    >
      <Text style={{ color: active ? colors.bgBase : colors.textMuted, fontSize: font.small, fontWeight: "600" }}>
        {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bgBase },
  scrollContent: { paddingHorizontal: spacing.lg, paddingTop: spacing.xl, paddingBottom: 112 },
  pageTitle: { color: colors.textPrimary, fontSize: font.h1, fontWeight: "800", letterSpacing: -0.8 },
  pageSubtitle: { color: colors.textMuted, fontSize: font.body, marginTop: 6, lineHeight: 22 },
  card: {
    backgroundColor: colors.bgSurface,
    borderColor: colors.border,
    borderWidth: 1,
    borderRadius: radius.lg,
    padding: 18,
    marginBottom: spacing.md,
  },
  button: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    borderWidth: 1,
    borderRadius: radius.sm,
    minHeight: 50,
    paddingVertical: 13,
    paddingHorizontal: spacing.lg,
  },
  buttonText: { fontSize: font.body, fontWeight: "700" },
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
    minHeight: 50,
    paddingVertical: 12,
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
