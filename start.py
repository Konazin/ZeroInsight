"""Inicializador unificado do ZeroInsight.

Sobe o servidor de desenvolvimento React (Vite) e o backend FastAPI,
abrindo o navegador automaticamente quando ambos estiverem prontos.

Uso:
    python start.py          # inicia tudo
    python start.py --no-frontend  # apenas o backend (sem npm)
"""
from __future__ import annotations

import argparse
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT / "frontend"
VITE_HOST = "127.0.0.1"
VITE_PORT = 5173


# ── Utilitários de rede ──────────────────────────────────────────────────────

def _port_listening(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def _wait_for_port(host: str, port: int, timeout: float = 40.0, label: str = "") -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _port_listening(host, port):
            return True
        time.sleep(0.4)
    print(f"[aviso] Timeout aguardando {label or f'{host}:{port}'}", file=sys.stderr)
    return False


# ── Gerenciamento do Vite ────────────────────────────────────────────────────

def _start_vite() -> subprocess.Popen | None:
    if not FRONTEND_DIR.is_dir():
        print("[aviso] Pasta frontend/ nao encontrada — apenas o backend sera iniciado.", file=sys.stderr)
        return None

    if _port_listening(VITE_HOST, VITE_PORT):
        print(f"[info]  Frontend ja esta rodando em http://{VITE_HOST}:{VITE_PORT}")
        return None  # already up, don't start another

    npm = "npm.cmd" if sys.platform == "win32" else "npm"
    try:
        print(f"[start] Iniciando frontend (npm run dev) na porta {VITE_PORT}...")
        flags: dict = {}
        if sys.platform == "win32":
            flags["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        return subprocess.Popen([npm, "run", "dev"], cwd=FRONTEND_DIR, **flags)
    except FileNotFoundError:
        print("[aviso] npm nao encontrado — apenas o backend sera iniciado.", file=sys.stderr)
        return None


def _stop_vite(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    print("[stop]  Encerrando frontend...")
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
            capture_output=True,
        )
    else:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()


# ── Ponto de entrada ─────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Inicia o ZeroInsight (backend + frontend)")
    parser.add_argument("--no-frontend", action="store_true", help="Inicia apenas o backend, sem npm")
    args = parser.parse_args()

    # Garante que o pacote zero_insight seja importavel
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

    vite_proc: subprocess.Popen | None = None

    if not args.no_frontend:
        vite_proc = _start_vite()

        if vite_proc is not None:
            print(f"[wait]  Aguardando frontend em http://{VITE_HOST}:{VITE_PORT}...")
            if _wait_for_port(VITE_HOST, VITE_PORT, label="Vite"):
                print(f"[ok]    Frontend pronto  -> http://{VITE_HOST}:{VITE_PORT}")
            else:
                print("[aviso] Iniciando backend mesmo assim.", file=sys.stderr)

    print("[start] Iniciando backend FastAPI...")
    from zero_insight.server.app import run_server

    try:
        run_server(open_browser=True)
    except KeyboardInterrupt:
        pass
    finally:
        if vite_proc is not None:
            _stop_vite(vite_proc)


if __name__ == "__main__":
    main()
