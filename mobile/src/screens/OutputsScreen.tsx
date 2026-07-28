import { useFocusEffect } from "@react-navigation/native";
import { FolderOpen, Trash2, X } from "lucide-react-native";
import { useCallback, useState } from "react";
import { Alert, Image, Modal, Pressable, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Card, PageTitle, Screen } from "../components/ui";
import { deleteCampaign, listCampaigns, type StoryResult } from "../lib/storyPipeline";
import { colors, font, radius, spacing } from "../theme";

export function OutputsScreen() {
  const [campaigns, setCampaigns] = useState<StoryResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [previewUri, setPreviewUri] = useState<string | null>(null);

  const refresh = useCallback(() => {
    setLoading(true);
    listCampaigns()
      .then(setCampaigns)
      .catch(() => setCampaigns([]))
      .finally(() => setLoading(false));
  }, []);

  useFocusEffect(
    useCallback(() => {
      refresh();
    }, [refresh]),
  );

  function confirmDelete(item: StoryResult) {
    Alert.alert("Excluir story?", "Esta ação remove as imagens do dispositivo.", [
      { text: "Cancelar", style: "cancel" },
      {
        text: "Excluir",
        style: "destructive",
        onPress: async () => {
          await deleteCampaign(item.directory);
          refresh();
        },
      },
    ]);
  }

  return (
    <Screen>
      <PageTitle title="Saídas" subtitle="Stories gerados e salvos neste dispositivo." />

      {loading ? (
        <Text style={styles.muted}>Carregando…</Text>
      ) : campaigns.length === 0 ? (
        <Card style={styles.empty}>
          <FolderOpen size={28} color={colors.textSubtle} />
          <Text style={styles.emptyText}>Nenhum story gerado ainda.</Text>
        </Card>
      ) : (
        campaigns.map((item) => (
          <Card key={item.campaign}>
            <View style={styles.cardHeader}>
              <View style={{ flex: 1 }}>
                <Text style={styles.campaignName}>{prettyName(item.campaign)}</Text>
                <Text style={styles.campaignMeta}>
                  {item.slides.length} slide(s) · {formatDate(item.createdAt)}
                </Text>
              </View>
              <Pressable onPress={() => confirmDelete(item)} hitSlop={8} style={styles.deleteBtn}>
                <Trash2 size={16} color={colors.danger} />
              </Pressable>
            </View>
            <View style={styles.thumbRow}>
              {item.slides.map((s, index) => (
                <Pressable
                  key={s.imageUri}
                  onPress={() => setPreviewUri(s.imageUri)}
                  accessibilityRole="imagebutton"
                  accessibilityLabel={`Ampliar slide ${index + 1}`}
                >
                  <Image source={{ uri: s.imageUri }} style={styles.thumb} />
                </Pressable>
              ))}
            </View>
          </Card>
        ))
      )}

      <Modal
        visible={Boolean(previewUri)}
        transparent={false}
        animationType="fade"
        onRequestClose={() => setPreviewUri(null)}
      >
        <SafeAreaView style={styles.previewModal}>
          <View style={styles.previewHeader}>
            <Text style={styles.previewTitle}>Visualização</Text>
            <Pressable
              onPress={() => setPreviewUri(null)}
              style={styles.closeButton}
              accessibilityRole="button"
              accessibilityLabel="Fechar visualização"
            >
              <X size={22} color={colors.textPrimary} />
            </Pressable>
          </View>
          {previewUri ? <Image source={{ uri: previewUri }} style={styles.previewImage} resizeMode="contain" /> : null}
          <Text style={styles.previewHint}>Toque no × para voltar às saídas.</Text>
        </SafeAreaView>
      </Modal>
    </Screen>
  );
}

function prettyName(campaign: string): string {
  const parts = campaign.split("_");
  parts.shift(); // remove timestamp
  return parts.join(" ").trim() || "Story";
}

function formatDate(ts: number): string {
  if (!ts) return "—";
  try {
    return new Date(ts).toLocaleDateString("pt-BR", { day: "2-digit", month: "short", year: "numeric" });
  } catch {
    return "—";
  }
}

const styles = StyleSheet.create({
  muted: { color: colors.textSubtle, fontSize: font.body },
  empty: { alignItems: "center", gap: spacing.md, paddingVertical: spacing.xl },
  emptyText: { color: colors.textMuted, fontSize: font.body },
  cardHeader: { flexDirection: "row", alignItems: "flex-start", marginBottom: spacing.md },
  campaignName: { color: colors.textPrimary, fontSize: font.h3, fontWeight: "600", textTransform: "capitalize" },
  campaignMeta: { color: colors.textSubtle, fontSize: font.small, marginTop: 2 },
  deleteBtn: {
    width: 32,
    height: 32,
    borderRadius: radius.sm,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.bgElevated,
    borderWidth: 1,
    borderColor: colors.border,
  },
  thumbRow: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  thumb: {
    width: 80,
    height: 142,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.bgElevated,
  },
  previewModal: { flex: 1, backgroundColor: colors.bgBase, padding: spacing.lg },
  previewHeader: {
    minHeight: 48,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: spacing.md,
  },
  previewTitle: { color: colors.textPrimary, fontSize: font.h3, fontWeight: "700" },
  closeButton: {
    width: 44,
    height: 44,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
  },
  previewImage: { flex: 1, width: "100%", borderRadius: radius.lg },
  previewHint: { color: colors.textSubtle, fontSize: font.small, textAlign: "center", paddingVertical: spacing.md },
});
