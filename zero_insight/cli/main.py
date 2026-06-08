"""CLI: menu interativo e comandos diretos."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rich.panel import Panel
from rich.table import Table

from zero_insight.cli.theme import ICONS, console


def configure_stdio() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zero-insight",
        description=(
            "ZeroInsight — startup juridica: "
            "dashboard Dino -> screenshot -> Groq Vision -> blog Markdown."
        ),
    )
    parser.add_argument("--run", action="store_true", help="Executa o pipeline sem menu")
    parser.add_argument("--check", action="store_true", help="Verifica CDP + Groq")
    parser.add_argument("--ui", action="store_true", help="Abre a interface desktop")
    parser.add_argument("--import-brand-doc", default="", help="Importa PDF/DOCX de comunicacao visual")
    parser.add_argument("--brand-name", default="", help="Nome da marca ao importar documento")
    parser.add_argument("--brand", default="", help="Marca/BrandProfile para --run ou --story")
    parser.add_argument("--list-ai-providers", action="store_true", help="Lista providers de IA")
    parser.add_argument("--test-ai-provider", default="", help="Testa provider no formato tipo:nome")
    parser.add_argument("--story", action="store_true", help="Gera pacote de Instagram Stories")
    parser.add_argument("--topic", default="", help="Tema da campanha de Stories")
    parser.add_argument("--objective", default="orientar com clareza", help="Objetivo dos Stories")
    parser.add_argument("--audience", default="publico juridico", help="Publico-alvo dos Stories")
    parser.add_argument("--tone", default="claro e responsavel", help="Tom de voz")
    parser.add_argument("--cta", default="Fale com a Requisite", help="CTA dos Stories")
    parser.add_argument("--slides", type=int, default=3, help="Quantidade de Stories")
    parser.add_argument("--template", default="", help="Template visual dos Stories")
    parser.add_argument("--from-dino", action="store_true", help="Tenta reutilizar metricas do Dino")
    parser.add_argument("--ai-text-provider", default="", help="Provider de texto para copy/roteiro")
    parser.add_argument("--ai-image-provider", default="", help="Provider de imagem para base visual")
    return parser


def cmd_check() -> int:
    from zero_insight.config import Settings
    from zero_insight.pipeline import test_cdp_sync, test_groq_sync

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


def cmd_run(brand: str = "") -> int:
    from zero_insight.config import Settings
    from zero_insight.pipeline import run_pipeline_sync

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
    ok, result = run_pipeline_sync(settings, on_log=on_log, brand=brand or None)

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


def cmd_story(args: argparse.Namespace) -> int:
    from zero_insight.config import Settings
    from zero_insight.content import StoryBrief
    from zero_insight.pipeline import run_story_pipeline_sync

    settings = Settings.from_env()
    brief = StoryBrief(
        topic=args.topic.strip() or "RPV Federal",
        objective=args.objective,
        audience=args.audience,
        tone=args.tone,
        cta=args.cta,
        slides=max(1, args.slides),
        template=args.template.strip() or settings.story_default_template,
        source="dino" if args.from_dino else "manual",
        brand_profile_id=args.brand or None,
        ai_text_provider=args.ai_text_provider or settings.default_text_provider,
        ai_image_provider=args.ai_image_provider or settings.default_image_provider,
    )

    def on_log(level: str, msg: str) -> None:
        style = {
            "INFO": "cyan",
            "SUCCESS": "green",
            "WARN": "yellow",
            "ERROR": "red",
            "STEP": "blue",
        }.get(level, "white")
        console.print(f"[{style}]{msg}[/{style}]")

    console.print(Panel("[step]Gerando pacote de Stories...[/step]", border_style="blue"))
    ok, manifest = run_story_pipeline_sync(
        settings,
        brief,
        from_dino=args.from_dino,
        on_log=on_log,
    )
    if manifest:
        outputs = manifest.get("outputs", {})
        console.print(f"[ok]Pasta: {outputs.get('directory', '')}[/ok]")
        console.print(f"[ok]Manifest: {outputs.get('manifest', '')}[/ok]")
        console.print(f"[ok]Review: {outputs.get('review', '')}[/ok]")
    return 0 if ok else 1


def cmd_import_brand_doc(args: argparse.Namespace) -> int:
    from zero_insight.config import Settings
    from zero_insight.services import BrandService

    settings = Settings.from_env()

    def on_log(level: str, msg: str) -> None:
        style = {"INFO": "cyan", "SUCCESS": "green", "WARN": "yellow", "ERROR": "red"}.get(level, "white")
        console.print(f"[{style}]{msg}[/{style}]")

    profile, path = BrandService(settings).import_document(
        Path(args.import_brand_doc),
        brand_name=args.brand_name or None,
        use_external_ai=False,
        on_log=on_log,
    )
    console.print(f"[ok]BrandProfile: {path}[/ok]")
    console.print(f"[ok]Marca: {profile.brand_name} ({profile.status})[/ok]")
    return 0


def cmd_list_ai_providers() -> int:
    from zero_insight.ai_providers import list_ai_providers

    for kind, providers in list_ai_providers().items():
        console.print(f"[bold]{kind}[/bold]: {', '.join(providers)}")
    return 0


def cmd_test_ai_provider(value: str) -> int:
    from zero_insight.ai_providers import test_provider

    if ":" not in value:
        console.print("[err]Use formato tipo:nome, exemplo text:custom[/err]")
        return 1
    kind, name = value.split(":", 1)
    ok, msg = test_provider(kind, name)
    console.print(("[ok]" if ok else "[err]") + msg + ("[/ok]" if ok else "[/err]"))
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    args = build_parser().parse_args(argv)

    if args.check:
        return cmd_check()
    if args.run:
        return cmd_run(args.brand)
    if args.import_brand_doc:
        return cmd_import_brand_doc(args)
    if args.list_ai_providers:
        return cmd_list_ai_providers()
    if args.test_ai_provider:
        return cmd_test_ai_provider(args.test_ai_provider)
    if args.ui:
        from zero_insight.desktop.app import main as desktop_main

        return desktop_main()
    if args.story:
        return cmd_story(args)

    from zero_insight.cli.terminal import launch

    launch()
    return 0
