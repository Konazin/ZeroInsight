from __future__ import annotations

import json
import sys
import traceback
from getpass import getpass
from pathlib import Path
from typing import Any

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from rich import box
from rich.columns import Columns
from rich.console import Group
from rich.json import JSON
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from zero_insight.cli.theme import ICONS, console
from zero_insight.config import GROQ_MODELS, GROQ_VISION_MODELS, PROJECT_ROOT, Settings, reload_settings, save_settings
from zero_insight.pipeline import run_pipeline_sync, run_story_pipeline_sync, test_cdp_sync, test_groq_sync

LEVEL_STYLE = {
    "INFO": "info",
    "STEP": "step",
    "SUCCESS": "ok",
    "WARN": "warn",
    "ERROR": "err",
}


def _is_interactive_tty() -> bool:
    return sys.stdin.isatty() and sys.stdout.isatty()


def _menu_select(message: str, choices: list[Choice], **kwargs: Any) -> str:
    if _is_interactive_tty():
        try:
            return inquirer.select(
                message=message,
                choices=choices,
                pointer=">",
                **kwargs,
            ).execute()
        except Exception as exc:
            console.print(f"[warn]Menu numerico: {exc}[/warn]")

    console.print(f"\n[bold]{message}[/bold]")
    for i, choice in enumerate(choices, 1):
        console.print(f"  {i}. {choice.name}")
    while True:
        raw = console.input("Opcao: ").strip()
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(choices):
                return choices[idx].value
        console.print("[err]Opcao invalida.[/err]")


def _menu_confirm(message: str, default: bool = True) -> bool:
    if _is_interactive_tty():
        try:
            return inquirer.confirm(message=message, default=default).execute()
        except Exception:
            pass
    hint = "S/n" if default else "s/N"
    raw = console.input(f"{message} ({hint}): ").strip().lower()
    if not raw:
        return default
    return raw in ("s", "sim", "y", "yes")


def _menu_text(message: str, default: str = "") -> str:
    if _is_interactive_tty():
        try:
            return inquirer.text(message=message, default=default).execute()
        except Exception:
            pass
    suffix = f" [{default}]" if default else ""
    raw = console.input(f"{message}{suffix}: ").strip()
    return raw or default


def _menu_secret(message: str) -> str:
    if _is_interactive_tty():
        try:
            return inquirer.secret(message=message).execute()
        except Exception:
            pass
    return getpass(f"{message}: ")


def _pause() -> None:
    console.print()
    console.input("[dim]Enter para voltar ao menu...[/dim] ")


def _story_defaults_path() -> Path:
    path = PROJECT_ROOT / ".zeroinsight_appdata" / "story_brief_defaults.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _load_story_defaults() -> dict[str, str]:
    path = _story_defaults_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {str(key): str(value) for key, value in data.items() if value is not None}
    except Exception:
        return {}


def _save_story_defaults(data: dict[str, object]) -> Path:
    path = _story_defaults_path()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _banner() -> None:
    console.clear()
    grid = Table.grid(expand=True)
    grid.add_column(ratio=1)
    grid.add_row(
        Text.from_markup(
            "[accent]ZeroInsight[/accent]\n"
            "[dim]Brave CDP  ->  extracao  ->  screenshot  ->  Groq  ->  blog[/dim]"
        )
    )
    console.print(
        Panel(
            grid,
            border_style="cyan",
            box=box.DOUBLE_EDGE,
            padding=(0, 2),
        )
    )
    console.print()


def _readiness_panel(settings: Settings) -> Panel:
    lines: list[str] = []
    if settings.groq_api_key.strip():
        lines.append(f"[ok]{ICONS['ok']}[/ok] Groq API key configurada")
    else:
        lines.append(
            f"[err]{ICONS['fail']}[/err] Groq API key ausente "
            "[dim](menu: Editar configuracao)[/dim]"
        )
    lines.append(
        f"[dim]{ICONS['arrow']}[/dim] Brave: execute [menu]scripts/start_brave_debug.bat[/menu]"
    )
    return Panel("\n".join(lines), title="[menu]Status rapido[/menu]", border_style="blue")


def _settings_table(settings: Settings) -> Table:
    table = Table(box=box.ROUNDED, show_header=True, header_style="accent")
    table.add_column("Configuracao", style="bold")
    table.add_column("Valor", overflow="fold")
    for label, value in [
        ("CDP", settings.cdp_url),
        ("URL alvo", settings.target_url),
        ("Modelo texto", settings.groq_model),
        ("Modelo visao", settings.groq_vision_model),
        ("OpenAI image", settings.openai_image_model),
        ("Provider imagem", settings.default_image_provider),
        ("Marca blog", settings.blog_brand_name),
        ("API key", settings.masked_api_key()),
        ("Saida", str(settings.output_path)),
        ("Posts", str(settings.posts_path)),
    ]:
        table.add_row(label, value)
    return table


def _format_log(level: str, msg: str) -> Text:
    style = LEVEL_STYLE.get(level, "white")
    icon = {
        "SUCCESS": ICONS["ok"],
        "ERROR": ICONS["fail"],
        "WARN": "!",
        "STEP": ICONS["arrow"],
    }.get(level, ".")
    return Text.from_markup(f"[{style}]{icon} {msg}[/{style}]")


class TerminalApp:
    """Interface interativa principal do projeto."""

    def __init__(self) -> None:
        self.settings = reload_settings()
        self._logs: list[Text] = []
        self._last_cdp: tuple[bool, str] | None = None
        self._last_groq: tuple[bool, str] | None = None

    def _on_log(self, level: str, msg: str) -> None:
        self._logs.append(_format_log(level, msg))

    def _home_layout(self) -> None:
        layout = Layout()
        layout.split_column(
            Layout(name="status", size=5),
            Layout(name="config"),
        )
        layout["status"].update(_readiness_panel(self.settings))
        layout["config"].update(
            Panel(_settings_table(self.settings), title="[menu]Configuracao[/menu]")
        )

        if self._last_cdp is not None or self._last_groq is not None:
            chips = Table.grid(padding=(0, 2))
            chips.add_column()
            chips.add_column()
            if self._last_cdp is not None:
                ok, _ = self._last_cdp
                chips.add_row(
                    "Brave",
                    f"[ok]{ICONS['ok']} OK[/ok]" if ok else f"[err]{ICONS['fail']} Falha[/err]",
                )
            if self._last_groq is not None:
                ok, _ = self._last_groq
                chips.add_row(
                    "Groq",
                    f"[ok]{ICONS['ok']} OK[/ok]" if ok else f"[err]{ICONS['fail']} Falha[/err]",
                )
            console.print(
                Panel(chips, title="[dim]Ultima verificacao[/dim]", border_style="dim")
            )

        console.print(layout)
        console.print()

    def _main_menu_choices(self) -> list[Choice]:
        run_hint = "" if self.settings.groq_api_key.strip() else " [dim](configure Groq)[/dim]"
        return [
            Choice("run", name=f"{ICONS['run']}  Executar pipeline{run_hint}"),
            Choice("stories_manual", name="▣  Gerar Stories sem Dino (visual + resumo salvo)"),
            Choice("preflight", name=f"{ICONS['check']}  Verificar conexoes (CDP + Groq)"),
            Choice("config", name=f"{ICONS['config']}  Ver configuracao completa"),
            Choice("edit", name=f"{ICONS['edit']}  Editar configuracao (.env)"),
            Choice("results", name=f"{ICONS['results']}  Historico de resultados"),
            Choice("help", name=f"{ICONS['help']}  Ajuda e pre-requisitos"),
            Choice("quit", name=f"{ICONS['quit']}  Sair"),
        ]

    def _run_pipeline_ui(self) -> None:
        if not self.settings.groq_api_key.strip():
            console.print(
                Panel(
                    "[warn]Configure GROQ_API_KEY antes de executar.[/warn]\n"
                    "Menu: Editar configuracao",
                    title="Configuracao incompleta",
                    border_style="yellow",
                )
            )
            _pause()
            return

        self._logs.clear()
        _banner()
        console.print(Panel("[step]Executando pipeline...[/step]", border_style="blue"))
        console.print()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=32),
            TaskProgressColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Iniciando...", total=5)

            def on_log(level: str, msg: str) -> None:
                self._on_log(level, msg)
                if "Conectando" in msg:
                    progress.update(task, completed=0, description="Conectando ao Brave...")
                elif "Extraindo" in msg:
                    progress.update(task, completed=1, description="Extraindo metricas...")
                elif "extraídos" in msg.lower() or "extraidos" in msg.lower():
                    progress.update(task, completed=2, description="Capturando screenshot...")
                elif "Screenshot" in msg:
                    progress.update(task, completed=2, description="Gerando post com IA...")
                elif "blog" in msg.lower() or "visao" in msg.lower():
                    progress.update(task, completed=3, description="Gerando post com IA...")
                elif "Markdown" in msg or "JSONL" in msg:
                    progress.update(task, completed=4, description="Salvando arquivos...")
                elif level == "SUCCESS" and "Post salvo" in msg:
                    progress.update(task, completed=5, description="Concluido!")

            ok, result = run_pipeline_sync(self.settings, on_log=on_log)
            progress.update(task, completed=5)

        log_content = Group(*self._logs) if self._logs else Text("Sem logs.", style="dim")
        console.print(Panel(log_content, title="Log da execucao", border_style="dim"))

        if ok and result:
            console.print()
            blog = result.get("blog_post", {})
            preview = (
                f"[bold]{blog.get('titulo', '')}[/bold]\n\n"
                f"{blog.get('subtitulo', '')}\n\n"
                f"[dim]{blog.get('meta_descricao', '')}[/dim]\n\n"
                f"Tags: {', '.join(blog.get('tags', []))}\n\n"
                f"Markdown: [cyan]{result.get('post_markdown', '')}[/cyan]\n"
                f"Screenshot: [cyan]{result.get('screenshot', '')}[/cyan]"
            )
            console.print(
                Panel(preview, title=f"[ok]Post gerado[/ok] · {result.get('source')}", border_style="green")
            )
            body = blog.get("corpo_markdown", "")
            if body:
                snippet = body[:600] + ("..." if len(body) > 600 else "")
                console.print(Panel(snippet, title="Trecho do post", border_style="dim"))
        else:
            console.print("\n[err]Pipeline nao concluido.[/err]")

        _pause()

    def _preflight_ui(self) -> None:
        _banner()
        console.print(Panel("[step]Verificando ambiente...[/step]", border_style="blue"))
        console.print()

        with console.status("[step]Testando Brave CDP...[/step]", spinner="dots"):
            self._last_cdp = test_cdp_sync(self.settings)
        with console.status("[step]Testando Groq API...[/step]", spinner="dots"):
            self._last_groq = test_groq_sync(self.settings)

        cdp_ok, cdp_msg = self._last_cdp
        groq_ok, groq_msg = self._last_groq

        table = Table(title="Diagnostico", box=box.ROUNDED, header_style="bold")
        table.add_column("Servico", style="bold")
        table.add_column("Status", justify="center")
        table.add_column("Detalhe", overflow="fold")
        table.add_row(
            "Brave CDP",
            f"[ok]{ICONS['ok']} OK[/ok]" if cdp_ok else f"[err]{ICONS['fail']} FALHA[/err]",
            cdp_msg,
        )
        table.add_row(
            "Groq API",
            f"[ok]{ICONS['ok']} OK[/ok]" if groq_ok else f"[err]{ICONS['fail']} FALHA[/err]",
            groq_msg,
        )
        console.print(table)

        if cdp_ok and groq_ok:
            console.print(
                Panel(
                    "[ok]Ambiente pronto![/ok] Pode executar o pipeline no menu principal.",
                    border_style="green",
                )
            )
        else:
            tips = []
            if not cdp_ok:
                tips.append(
                    "- Brave: execute [cyan]scripts\\start_brave_debug.bat[/cyan]"
                )
            if not groq_ok:
                tips.append("- Groq: configure a chave em [menu]Editar configuracao[/menu]")
            console.print(
                Panel("\n".join(tips), title="[warn]Como corrigir[/warn]", border_style="yellow")
            )

        _pause()

    def _show_config(self) -> None:
        _banner()
        console.print(Panel(_settings_table(self.settings), title="Configuracao atual"))
        _pause()

    def _run_manual_stories_ui(self) -> None:
        from zero_insight.content import StoryBrief
        from zero_insight.services import BrandService

        _banner()
        console.print(
            Panel(
                "Gera Stories sem acessar Dino. Informe o PDF/DOCX/imagem da identidade visual "
                "e um resumo do que a empresa faz.",
                title="[menu]Stories sem Dino[/menu]",
                border_style="blue",
            )
        )
        defaults = _load_story_defaults()
        if defaults:
            console.print(f"[dim]Usando defaults de {_story_defaults_path()}[/dim]")
        brand_doc = _menu_text(
            "Caminho do PDF/DOCX/imagem da identidade visual",
            defaults.get("brand_doc", ""),
        )
        if not brand_doc:
            console.print("[warn]Caminho nao informado.[/warn]")
            _pause()
            return
        brand_path = Path(brand_doc).expanduser()
        if not brand_path.exists():
            console.print(f"[err]Arquivo nao encontrado: {brand_path}[/err]")
            _pause()
            return

        brand_name = _menu_text("Nome da marca", defaults.get("brand_name", brand_path.stem))
        company_summary = _menu_text(
            "Resumo do que a empresa faz",
            defaults.get(
                "company_summary",
                "empresa de servicos profissionais com comunicacao clara e confiavel",
            ),
        )
        topic = _menu_text("Tema do Story", defaults.get("topic", f"Conheca {brand_name}"))
        cta = _menu_text("CTA", defaults.get("cta", f"Fale com {brand_name}"))
        slides_raw = _menu_text("Quantidade de Stories", defaults.get("slides", "1"))
        try:
            slides = max(1, min(10, int(slides_raw)))
        except ValueError:
            slides = 1

        image_provider = _menu_select(
            "Provider de imagem",
            [
                Choice("local", name="Local sem API (recomendado)"),
                Choice("mock", name="Mock local simples"),
                Choice("openai", name="OpenAI (pago/API)"),
                Choice("custom", name="Custom OpenAI-compatible"),
                Choice("stability", name="Stability"),
                Choice("replicate", name="Replicate"),
            ],
            default=defaults.get("image_provider", "local"),
        )
        if image_provider == "openai" and not self.settings.openai_api_key.strip():
            key = _menu_secret("OPENAI_API_KEY nao configurada. Informe a chave")
            if key.strip():
                self.settings.openai_api_key = key.strip()
                self.settings.default_image_provider = "openai"
                save_settings(self.settings)
                self.settings = reload_settings()

        self._logs.clear()
        defaults_path = _save_story_defaults(
            {
                "brand_doc": str(brand_path),
                "brand_name": brand_name,
                "company_summary": company_summary,
                "topic": topic,
                "cta": cta,
                "slides": str(slides),
                "image_provider": image_provider,
            }
        )
        console.print(f"[dim]Dados salvos para reutilizacao: {defaults_path}[/dim]")

        def on_log(level: str, msg: str) -> None:
            self._on_log(level, msg)
            style = LEVEL_STYLE.get(level, "white")
            console.print(f"[{style}]{msg}[/{style}]")

        try:
            with console.status("[step]Importando identidade visual...[/step]", spinner="dots"):
                profile, profile_path = BrandService(self.settings).import_document(
                    brand_path,
                    brand_name=brand_name,
                    use_external_ai=False,
                    on_log=on_log,
                )

            brief = StoryBrief(
                topic=topic,
                objective="gerar uma imagem de post para Stories alinhada a identidade visual",
                audience="publico-alvo da empresa",
                tone="claro, profissional e coerente com a marca",
                cta=cta,
                slides=slides,
                template=self.settings.story_default_template,
                source="manual_story_post",
                brand_profile_id=str(profile_path),
                ai_text_provider="mock",
                ai_image_provider=image_provider,
                company_summary=company_summary,
            )

            console.print(
                Panel(
                    f"Marca: [bold]{profile.brand_name}[/bold]\n"
                    f"Provider imagem: [bold]{image_provider}[/bold]\n"
                    f"Sem Dino: [bold]sim[/bold]",
                    title="[step]Gerando Stories[/step]",
                    border_style="blue",
                )
            )
            ok, manifest = run_story_pipeline_sync(
                self.settings,
                brief,
                from_dino=False,
                on_log=on_log,
            )
        except Exception as exc:
            console.print(
                Panel(
                    f"[err]{exc}[/err]\n\n[dim]{traceback.format_exc()}[/dim]",
                    title="Falha ao gerar Stories",
                    border_style="red",
                )
            )
            _pause()
            return

        if manifest:
            outputs = manifest.get("outputs", {})
            if outputs.get("review") and outputs.get("manifest"):
                console.print(
                    Panel(
                        f"Pasta: [cyan]{outputs.get('directory', '')}[/cyan]\n"
                        f"Review: [cyan]{outputs.get('review', '')}[/cyan]\n"
                        f"Manifest: [cyan]{outputs.get('manifest', '')}[/cyan]",
                        title="[ok]Stories gerados[/ok]" if ok else "[warn]Stories gerados com avisos[/warn]",
                        border_style="green" if ok else "yellow",
                    )
                )
            else:
                console.print(
                    Panel(
                        f"Pasta parcial: [cyan]{outputs.get('directory', '')}[/cyan]\n"
                        "Review/manifest final nao foram criados. Veja o erro acima.",
                        title="[err]Stories nao concluidos[/err]",
                        border_style="red",
                    )
                )
        _pause()

    def _edit_config(self) -> None:
        _banner()
        field = _menu_select(
            "Qual campo deseja editar?",
            [
                Choice("cdp_port", name="Porta CDP (Brave)"),
                Choice("target_url", name="URL alvo"),
                Choice("groq_api_key", name="Chave Groq API"),
                Choice("openai_api_key", name="Chave OpenAI API"),
                Choice("default_image_provider", name="Provider padrao de imagem"),
                Choice("openai_image_model", name="Modelo OpenAI para imagem"),
                Choice("groq_model", name="Modelo Groq (texto)"),
                Choice("groq_vision_model", name="Modelo Groq (visao / blog)"),
                Choice("blog_brand_name", name="Nome da startup no blog"),
                Choice("groq_endpoint", name="Endpoint Groq"),
                Choice("output_file", name="Arquivo de saida"),
                Choice("back", name="<- Voltar sem salvar"),
            ],
        )

        if field == "back":
            return

        if field == "groq_model":
            value = _menu_select(
                "Modelo Groq (texto)",
                [Choice(m, name=m) for m in GROQ_MODELS],
            )
        elif field == "groq_vision_model":
            value = _menu_select(
                "Modelo Groq (visao)",
                [Choice(m, name=m) for m in GROQ_VISION_MODELS],
            )
        elif field == "default_image_provider":
            value = _menu_select(
                "Provider padrao de imagem",
                [
                    Choice("local", name="local (sem API, recomendado)"),
                    Choice("mock", name="mock (sem custo/API, simples)"),
                    Choice("openai", name="openai (pago/API)"),
                    Choice("custom", name="custom OpenAI-compatible"),
                    Choice("stability", name="stability"),
                    Choice("replicate", name="replicate"),
                ],
            )
        elif field == "blog_brand_name":
            value = _menu_text(
                "Nome da startup juridica no blog",
                self.settings.blog_brand_name,
            )
        elif field == "groq_api_key":
            value = _menu_secret("Chave Groq API (gsk_...)")
        elif field == "openai_api_key":
            value = _menu_secret("Chave OpenAI API (sk-...)")
        else:
            defaults = {
                "cdp_port": self.settings.cdp_port,
                "target_url": self.settings.target_url,
                "groq_endpoint": self.settings.groq_endpoint,
                "output_file": self.settings.output_file,
                "blog_brand_name": self.settings.blog_brand_name,
                "openai_image_model": self.settings.openai_image_model,
                "default_image_provider": self.settings.default_image_provider,
            }
            value = _menu_text(
                f"Novo valor para {field}",
                defaults.get(field, ""),
            )

        setattr(self.settings, field, value.strip() if isinstance(value, str) else value)
        save_settings(self.settings)
        self.settings = reload_settings()
        console.print("\n[ok]Configuracao salva em .env[/ok]")
        _pause()

    def _show_results(self) -> None:
        _banner()
        path = self.settings.output_path

        if not path.exists():
            console.print(
                Panel(
                    "[warn]Nenhum resultado ainda.[/warn]\n"
                    "Execute o pipeline para gerar registros.",
                    border_style="yellow",
                )
            )
            _pause()
            return

        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        recent = lines[-5:]

        table = Table(
            title=f"Ultimos {len(recent)} registros · {path.name}",
            box=box.SIMPLE_HEAD,
            header_style="accent",
        )
        table.add_column("#", style="dim", width=3)
        table.add_column("Horario", style="cyan")
        table.add_column("Resumo")
        table.add_column("Metrica", justify="right")

        for i, line in enumerate(recent, 1):
            try:
                row: dict[str, Any] = json.loads(line)
                blog = row.get("blog_post", {})
                output = row.get("output", {})
                if blog.get("titulo"):
                    resumo = str(blog.get("titulo", ""))[:40]
                    metrica = str(blog.get("meta_descricao", ""))[:50]
                elif "visualizacoes" in output:
                    resumo = output.get("titulo") or row.get("source", "dino")
                    metrica = (
                        f"views {output.get('visualizacoes')} | "
                        f"dist. {output.get('distribuicoes_realizadas')}"
                    )
                else:
                    resumo = str(output.get("cliente", "-"))
                    metrica = str(output.get("valor", output.get("status", "-")))
                table.add_row(
                    str(i),
                    row.get("timestamp", "")[:19].replace("T", " "),
                    resumo[:40],
                    metrica,
                )
            except json.JSONDecodeError:
                table.add_row(str(i), "-", "linha invalida", "-", "-")

        console.print(table)

        if recent:
            console.print()
            try:
                last = json.loads(recent[-1])
                console.print(
                    Panel(
                        JSON.from_data(last, indent=2),
                        title="Ultimo registro (completo)",
                        border_style="dim",
                    )
                )
            except json.JSONDecodeError:
                pass

        _pause()

    def _show_help(self) -> None:
        _banner()
        steps = Table(box=box.MINIMAL, show_header=False, padding=(0, 2))
        steps.add_column(style="accent", width=3)
        steps.add_column()
        for num, text in [
            ("1", "Execute scripts/start_brave_debug.bat e faca login no Dino"),
            ("2", "Copie .env.example para .env e configure GROQ_API_KEY"),
            ("3", "Use Verificar conexoes no menu"),
            ("4", "Execute o pipeline — posts em posts/ e log em results.jsonl"),
        ]:
            steps.add_row(num, text)

        console.print(
            Columns(
                [
                    Panel(steps, title="[menu]Passo a passo[/menu]", border_style="cyan"),
                    Panel(
                        "[bold]CLI[/bold]\n"
                        "[dim]python main.py[/dim]\n"
                        "[dim]python main.py --check[/dim]\n"
                        "[dim]python main.py --run[/dim]\n"
                        "[dim]python -m zero_insight[/dim]\n\n"
                        f"[bold]CDP[/bold]\n"
                        f"Porta padrao: {self.settings.cdp_port}",
                        title="[menu]Referencia[/menu]",
                        border_style="blue",
                    ),
                ],
                equal=True,
            )
        )
        _pause()

    def _dispatch(self, action: str) -> None:
        handlers = {
            "run": self._run_pipeline_ui,
            "stories_manual": self._run_manual_stories_ui,
            "preflight": self._preflight_ui,
            "config": self._show_config,
            "edit": self._edit_config,
            "results": self._show_results,
            "help": self._show_help,
        }
        try:
            handler = handlers.get(action)
            if handler:
                handler()
        except KeyboardInterrupt:
            console.print("\n[dim]Acao cancelada.[/dim]")
            _pause()
        except Exception as exc:
            _banner()
            console.print(
                Panel(
                    f"[err]{exc}[/err]\n\n[dim]{traceback.format_exc()}[/dim]",
                    title="Erro inesperado",
                    border_style="red",
                )
            )
            _pause()

    def run(self) -> None:
        while True:
            _banner()
            self._home_layout()
            console.print(Rule("[dim]Menu principal[/dim]", style="dim"))

            action = _menu_select(
                "O que deseja fazer?",
                self._main_menu_choices(),
                qmark="",
                amark="",
            )

            if action == "quit":
                if _menu_confirm("Deseja sair?", default=True):
                    console.print("\n[dim]Ate logo.[/dim]\n")
                    break
                continue

            self._dispatch(action)
            self.settings = reload_settings()


def launch() -> None:
    try:
        TerminalApp().run()
    except KeyboardInterrupt:
        console.print("\n[dim]Interrompido.[/dim]\n")
    except Exception as exc:
        console.print(
            Panel(
                f"[err]{exc}[/err]\n\n[dim]{traceback.format_exc()}[/dim]",
                title="Falha ao iniciar a UI",
                border_style="red",
            )
        )
        raise
