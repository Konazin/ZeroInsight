import { useFocusEffect } from "@react-navigation/native";
import { FolderOpen, Trash2 } from "lucide-react-native";
import { useCallback, useState } from "react";
import { Alert, Image, Pressable, StyleSheet, Text, View } from "react-native";
import { Card, PageTitle, Screen } from "../components/ui";
import { deleteCampaign, listCampaigns, type StoryResult } from "../lib/storyPipeline";
import { colors, font, radius, spacing } from "../theme";

export function OutputsScreen() {
  const [campaigns, setCampaigns] = useState<StoryResult[]>([]);
  const [loading, setLoading] = useState(true);

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
              {item.slides.map((s) => (
                <Image key={s.imageUri} source={{ uri: s.imageUri }} style={styles.thumb} />
              ))}
            </View>
          </Card>
        ))
      )}
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
    backgroundColor: "rgba(239,68,68,0.10)",
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
});
