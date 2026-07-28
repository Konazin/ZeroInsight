import { createBottomTabNavigator } from "@react-navigation/bottom-tabs";
import { NavigationContainer, type Theme } from "@react-navigation/native";
import { FolderOpen, Home, Settings as SettingsIcon, Sparkles } from "lucide-react-native";
import { DashboardScreen } from "../screens/DashboardScreen";
import { GenerateStoryScreen } from "../screens/GenerateStoryScreen";
import { OutputsScreen } from "../screens/OutputsScreen";
import { SettingsScreen } from "../screens/SettingsScreen";
import { colors, font } from "../theme";

const Tab = createBottomTabNavigator();

const navTheme: Theme = {
  dark: true,
  colors: {
    primary: colors.accent,
    background: colors.bgBase,
    card: colors.bgOverlay,
    text: colors.textPrimary,
    border: colors.borderSubtle,
    notification: colors.accent,
  },
};

export function RootNavigator() {
  return (
    <NavigationContainer theme={navTheme}>
      <Tab.Navigator
        screenOptions={{
          headerShown: false,
          tabBarStyle: {
            backgroundColor: colors.bgOverlay,
            borderTopColor: colors.borderSubtle,
            height: 72,
            paddingBottom: 10,
            paddingTop: 8,
          },
          tabBarActiveTintColor: colors.textPrimary,
          tabBarInactiveTintColor: colors.textSubtle,
          tabBarLabelStyle: { fontSize: font.tiny, fontWeight: "700" },
          tabBarItemStyle: { borderRadius: 12, marginHorizontal: 3 },
        }}
      >
        <Tab.Screen
          name="Dashboard"
          component={DashboardScreen}
          options={{ title: "Início", tabBarIcon: ({ color }) => <Home size={20} color={color} /> }}
        />
        <Tab.Screen
          name="Generate"
          component={GenerateStoryScreen}
          options={{ title: "Gerar", tabBarIcon: ({ color }) => <Sparkles size={20} color={color} /> }}
        />
        <Tab.Screen
          name="Outputs"
          component={OutputsScreen}
          options={{ title: "Saídas", tabBarIcon: ({ color }) => <FolderOpen size={20} color={color} /> }}
        />
        <Tab.Screen
          name="Settings"
          component={SettingsScreen}
          options={{ title: "Config", tabBarIcon: ({ color }) => <SettingsIcon size={20} color={color} /> }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
