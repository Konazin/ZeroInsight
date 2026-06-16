from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QFormLayout, QLineEdit, QWidget

from zero_insight.config import Settings


class ConfigForm(QWidget):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.fields: dict[str, QLineEdit] = {}
        layout = QFormLayout(self)
        for key, label in [
            ("target_url", "URL dashboard Dino"),
            ("cdp_port", "Porta CDP"),
            ("brave_executable_path", "Caminho brave.exe"),
            ("output_dir", "Diretorio base de saida"),
            ("groq_api_key", "GROQ API key"),
            ("blog_brand_name", "Marca blog"),
            ("story_brand_name", "Marca Stories"),
            ("story_brand_primary_color", "Cor primaria"),
            ("story_brand_secondary_color", "Cor secundaria"),
            ("story_logo_path", "Logo"),
            ("local_image_model_path", "Modelo local de imagem"),
        ]:
            field = QLineEdit(str(getattr(settings, key, "")))
            if key == "groq_api_key":
                field.setEchoMode(QLineEdit.EchoMode.Password)
            self.fields[key] = field
            layout.addRow(label, field)

    def values(self) -> dict[str, Any]:
        return {key: field.text().strip() for key, field in self.fields.items()}
