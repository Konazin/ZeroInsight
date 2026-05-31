"""Tema visual compartilhado do terminal."""

from rich.console import Console
from rich.theme import Theme

APP_THEME = Theme(
    {
        "info": "cyan",
        "step": "blue",
        "ok": "bold green",
        "warn": "yellow",
        "err": "bold red",
        "dim": "dim",
        "accent": "bold cyan",
        "menu": "bold white",
    }
)

console = Console(theme=APP_THEME, highlight=False)

ICONS = {
    "run": ">",
    "check": "?",
    "config": "*",
    "edit": "+",
    "results": "#",
    "help": "!",
    "quit": "x",
    "ok": "+",
    "fail": "-",
    "arrow": ">",
}
