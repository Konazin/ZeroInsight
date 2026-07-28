import { StatusBar } from "expo-status-bar";
import { SafeAreaProvider } from "react-native-safe-area-context";
import { ConfigProvider } from "./src/context/ConfigContext";
import { RootNavigator } from "./src/navigation/RootNavigator";

export default function App() {
  return (
    <SafeAreaProvider>
      <ConfigProvider>
        <StatusBar style="light" backgroundColor="#070707" />
        <RootNavigator />
      </ConfigProvider>
    </SafeAreaProvider>
  );
}
