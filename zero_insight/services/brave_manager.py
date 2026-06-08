from __future__ import annotations

import os
import shutil
import subprocess
import sys
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib.parse import quote

import httpx

from zero_insight.config import Settings

LogCallback = Callable[[str, str], None]

BRAVE_DOWNLOAD_URL = "https://brave.com/download/"
BRAVE_WINGET_IDS = ("Brave.Brave", "BraveSoftware.BraveBrowser")


@dataclass
class BraveStatus:
    installed: bool
    path: str
    cdp_connected: bool
    message: str


def default_app_data_dir() -> Path:
    configured = os.getenv("ZEROINSIGHT_APP_DATA_DIR", "").strip()
    if configured:
        return Path(configured).expanduser()
    base = os.getenv("LOCALAPPDATA") or os.getenv("APPDATA") or str(Path.home())
    return Path(base) / "ZeroInsight"


class BraveManager:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.app_data_dir = Path(settings.app_data_dir or default_app_data_dir())
        self.profile_dir = self.app_data_dir / "brave-profile"

    def find_brave_executable(self) -> Path | None:
        configured = self.settings.brave_executable_path.strip()
        candidates = []
        if configured:
            candidates.append(Path(configured))
        local_app = os.getenv("LOCALAPPDATA", "")
        candidates.extend(
            [
                Path("C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"),
                Path("C:/Program Files (x86)/BraveSoftware/Brave-Browser/Application/brave.exe"),
                Path(local_app) / "BraveSoftware/Brave-Browser/Application/brave.exe",
            ]
        )
        for candidate in candidates:
            if candidate.is_file():
                return candidate

        found = shutil.which("brave") or shutil.which("brave.exe")
        if found:
            return Path(found)

        registry_path = self._find_brave_in_registry()
        if registry_path:
            return registry_path
        return None

    def _find_brave_in_registry(self) -> Path | None:
        if sys.platform != "win32":
            return None
        try:
            import winreg
        except ImportError:
            return None
        keys = (
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\brave.exe",
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\brave.exe",
        )
        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
            for key in keys:
                try:
                    with winreg.OpenKey(root, key) as handle:
                        value, _ = winreg.QueryValueEx(handle, None)
                    path = Path(value)
                    if path.is_file():
                        return path
                except OSError:
                    continue
        return None

    def is_brave_installed(self) -> bool:
        return self.find_brave_executable() is not None

    def is_winget_available(self) -> bool:
        return shutil.which("winget") is not None

    def install_brave_with_winget(self, on_log: LogCallback | None = None) -> bool:
        if not self.is_winget_available():
            if on_log:
                on_log("WARN", "winget nao encontrado neste Windows.")
            return False
        for package_id in BRAVE_WINGET_IDS:
            cmd = ["winget", "install", "-e", "--id", package_id]
            if on_log:
                on_log("INFO", "Executando: " + " ".join(cmd))
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            assert proc.stdout is not None
            for line in proc.stdout:
                if on_log and line.strip():
                    on_log("INFO", line.strip())
            code = proc.wait()
            if code == 0 and self.is_brave_installed():
                if on_log:
                    on_log("SUCCESS", "Brave instalado com winget.")
                return True
            if on_log:
                on_log("WARN", f"winget retornou codigo {code} para {package_id}.")
        return False

    def open_brave_download_page(self) -> None:
        webbrowser.open(BRAVE_DOWNLOAD_URL)

    def start_brave_with_cdp(self, on_log: LogCallback | None = None) -> bool:
        brave_path = self.find_brave_executable()
        if not brave_path:
            if on_log:
                on_log("ERROR", "Brave nao encontrado. Instale o Brave primeiro.")
            return False
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        cmd = [
            str(brave_path),
            f"--remote-debugging-port={self.settings.cdp_port}",
            f"--user-data-dir={self.profile_dir}",
            "--remote-allow-origins=http://localhost",
            self.settings.target_url,
        ]
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if on_log:
            on_log("SUCCESS", "Brave dedicado iniciado. Faca login manual no Dino.")
        return True

    def test_cdp_connection(self) -> tuple[bool, str]:
        try:
            res = httpx.get(f"{self.settings.cdp_url}/json/version", timeout=5.0)
            if res.is_success:
                return True, f"CDP conectado: {res.json().get('Browser', 'Brave')}"
            return False, f"CDP respondeu HTTP {res.status_code}"
        except Exception as exc:
            return False, f"CDP indisponivel em {self.settings.cdp_url}: {exc}"

    def open_url_in_cdp_brave(self, url: str | None = None) -> tuple[bool, str]:
        target = url or self.settings.target_url
        try:
            res = httpx.put(
                f"{self.settings.cdp_url}/json/new?{quote(target, safe=':/?&=%')}",
                timeout=5.0,
            )
            if res.is_success:
                return True, "Dashboard enviado para o Brave com CDP."
        except Exception:
            pass
        if self.start_brave_with_cdp():
            return True, "Brave iniciado com o dashboard. Faca login manual se necessario."
        return False, "Nao foi possivel abrir o dashboard no Brave dedicado."

    def get_status(self) -> BraveStatus:
        path = self.find_brave_executable()
        cdp_ok, cdp_msg = self.test_cdp_connection()
        if path:
            return BraveStatus(True, str(path), cdp_ok, cdp_msg)
        return BraveStatus(False, "", cdp_ok, "Brave nao encontrado nos caminhos comuns.")
