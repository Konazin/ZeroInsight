"""CLI: menu interativo e comandos diretos."""

from __future__ import annotations

import argparse
import sys

from rich.panel import Panel
from rich.table import Table

from automacao_posts.cli.theme import ICONS, console


def configure_stdio() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="automacao-posts",
        description=(
            "Automacao de posts para startup juridica: "
            "dashboard Dino -> screenshot -> Groq Vision -> blog Markdown."
        ),
    )
    parser.add_argument("--run", action="store_true", help="Executa o pipeline sem menu")
    parser.add_argument("--check", action="store_true", help="Verifica CDP + Groq")
    return parser


def cmd_check() -> int:
    from automacao_posts.config import Settings
    from automacao_posts.pipeline import test_cdp_sync, test_groq_sync

    settings = Settings.from_env()
    console.print(Panel("[step]Verificando ambiente...[/step]", border_style="blue"))

    cdp_ok, cdp_msg = test_cdp_sync(settings)
    groq_ok, groq_msg = test_groq_sync(settings)

    table = Table(show_header=True, header_style="bold")
    table.add_column("Servico")
    table.add_column("Status")
    table.add_column("Detalhe")
    table.add_row(
        "Brave CDP",
        f"OK ({ICONS['ok']})" if cdp_ok else f"FALHA ({ICONS['fail']})",
        cdp_msg,
    )
    table.add_row(
        "Groq API",
        f"OK ({ICONS['ok']})" if groq_ok else f"FALHA ({ICONS['fail']})",
        groq_msg,
    )
    console.print(table)

    if cdp_ok and groq_ok:
        console.print("\n[ok]Ambiente pronto.[/ok]")
        return 0
    console.print("\n[err]Corrija os itens em falha.[/err]")
    return 1


def cmd_run() -> int:
    from automacao_posts.config import Settings
    from automacao_posts.pipeline import run_pipeline_sync

    settings = Settings.from_env()
    if not settings.groq_api_key.strip():
        console.print("[err]GROQ_API_KEY nao configurada no .env[/err]")
        return 1

    def on_log(level: str, msg: str) -> None:
        style = {"INFO": "cyan", "SUCCESS": "green", "WARN": "yellow", "ERROR": "red"}.get(
            level, "white"
        )
        console.print(f"[{style}]{msg}[/{style}]")

    console.print(Panel("[step]Executando pipeline...[/step]", border_style="blue"))
    ok, result = run_pipeline_sync(settings, on_log=on_log)

    if ok and result:
        console.print(f"\n[ok]Registro: {settings.output_path}[/ok]")
        console.print(f"[ok]Post: {result.get('post_markdown', '')}[/ok]")
        console.print(f"[ok]Screenshot: {result.get('screenshot', '')}[/ok]")
        blog = result.get("blog_post", {})
        if blog.get("titulo"):
            console.print(f"[ok]Titulo: {blog['titulo']}[/ok]")
        return 0
    console.print("\n[err]Pipeline falhou.[/err]")
    return 1


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    args = build_parser().parse_args(argv)

    if args.check:
        return cmd_check()
    if args.run:
        return cmd_run()

    from automacao_posts.cli.terminal import launch

    launch()
    return 0
