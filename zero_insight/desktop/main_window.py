from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import QThread
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from zero_insight.config import Settings
from zero_insight.content import StoryBrief
from zero_insight.desktop.dialogs import show_actionable_error
from zero_insight.desktop.state import DesktopState
from zero_insight.desktop.workers import Worker
from zero_insight.desktop.widgets import ConfigForm, LogViewer, StatusCard
from zero_insight.services import (
    BraveManager,
    EnvironmentService,
    OutputService,
    PipelineService,
    SettingsService,
    BrandService,
)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ZeroInsight")
        self.resize(1180, 760)

        self.settings_service = SettingsService()
        self.settings = self.settings_service.load()
        self.state = DesktopState()
        self.threads: list[QThread] = []
        self.action_buttons: list[QPushButton] = []

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(210)
        self.stack = QStackedWidget()
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress_label = QLabel("Pronto")
        self.progress_label.setObjectName("Muted")
        self.logs = LogViewer()

        for name in [
            "Dashboard",
            "Ambiente",
            "Brave",
            "Marcas",
            "IA / Providers",
            "Gerar Post",
            "Gerar Stories",
            "Saidas",
            "Configuracoes",
            "Logs",
        ]:
            self.sidebar.addItem(QListWidgetItem(name))

        self._build_pages()
        self.sidebar.currentRowChanged.connect(self.stack.setCurrentIndex)
        self.sidebar.setCurrentRow(0)

        footer = QHBoxLayout()
        footer.addWidget(self.progress)
        footer.addWidget(self.progress_label)

        main_layout = QVBoxLayout()
        content = QHBoxLayout()
        content.addWidget(self.sidebar)
        content.addWidget(self.stack, 1)
        main_layout.addLayout(content, 1)
        main_layout.addLayout(footer)

        root = QWidget()
        root.setLayout(main_layout)
        self.setCentralWidget(root)
        self.refresh_dashboard()

    def _build_pages(self) -> None:
        self.stack.addWidget(self._scroll_page(self._dashboard_page()))
        self.stack.addWidget(self._scroll_page(self._environment_page()))
        self.stack.addWidget(self._scroll_page(self._brave_page()))
        self.stack.addWidget(self._scroll_page(self._brands_page()))
        self.stack.addWidget(self._scroll_page(self._providers_page()))
        self.stack.addWidget(self._scroll_page(self._post_page()))
        self.stack.addWidget(self._scroll_page(self._stories_page()))
        self.stack.addWidget(self._scroll_page(self._outputs_page()))
        self.stack.addWidget(self._scroll_page(self._settings_page()))
        self.stack.addWidget(self.logs)

    @staticmethod
    def _scroll_page(page: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setWidget(page)
        return scroll

    def _page(self, title: str) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel(title)
        label.setObjectName("Title")
        title_font = QFont("Segoe UI")
        title_font.setPointSize(18)
        title_font.setWeight(QFont.Weight.Bold)
        label.setFont(title_font)
        layout.addWidget(label)
        return page, layout

    def _dashboard_page(self) -> QWidget:
        page, layout = self._page("Dashboard")
        self.cards = {
            "brave": StatusCard("Brave instalado"),
            "cdp": StatusCard("Brave/CDP conectado"),
            "url": StatusCard("URL configurada"),
            "api": StatusCard("API configurada"),
            "last_run": StatusCard("Ultima execucao"),
            "last_output": StatusCard("Ultimo output"),
        }
        grid = QGridLayout()
        for idx, card in enumerate(self.cards.values()):
            grid.addWidget(card, idx // 3, idx % 3)
        layout.addLayout(grid)

        actions = QHBoxLayout()
        self._add_action(actions, "Verificar ambiente", self.run_environment_check)
        self._add_action(actions, "Iniciar Brave", self.start_brave)
        self._add_action(actions, "Gerar Stories", lambda: self.sidebar.setCurrentRow(6))
        self._add_action(actions, "Abrir saida", self.open_output_root)
        actions.addStretch(1)
        layout.addLayout(actions)
        layout.addStretch(1)
        return page

    def _environment_page(self) -> QWidget:
        page, layout = self._page("Ambiente")
        self.env_results = QVBoxLayout()
        self._add_action(layout, "Rodar check de ambiente", self.run_environment_check)
        layout.addLayout(self.env_results)
        layout.addStretch(1)
        return page

    def _brave_page(self) -> QWidget:
        page, layout = self._page("Brave")
        self.brave_status = QLabel("Status ainda nao verificado.")
        self.brave_status.setWordWrap(True)
        self.brave_status.setObjectName("Muted")
        layout.addWidget(self.brave_status)
        actions = QHBoxLayout()
        self._add_action(actions, "Detectar Brave", self.refresh_brave_status)
        self._add_action(actions, "Instalar Brave", self.install_brave)
        self._add_action(actions, "Iniciar Brave para ZeroInsight", self.start_brave)
        self._add_action(actions, "Testar CDP", self.test_cdp)
        self._add_action(actions, "Abrir dashboard Dino", self.open_dino)
        actions.addStretch(1)
        layout.addLayout(actions)
        notice = QLabel("Login, captcha e MFA continuam manuais. O app usa perfil dedicado em APPDATA/LOCALAPPDATA.")
        notice.setObjectName("Muted")
        notice.setWordWrap(True)
        layout.addWidget(notice)
        layout.addStretch(1)
        return page

    def _post_page(self) -> QWidget:
        page, layout = self._page("Gerar Post")
        group = QGroupBox("Post Markdown")
        form = QFormLayout(group)
        self.post_url = QLineEdit(self.settings.target_url)
        self.post_brand = QComboBox()
        self._fill_brand_combo(self.post_brand)
        form.addRow("URL alvo", self.post_url)
        form.addRow("Marca", self.post_brand)
        self.post_validate_brand = QCheckBox("validar comunicacao visual")
        self.post_validate_brand.setChecked(True)
        form.addRow("Validacao", self.post_validate_brand)
        self._add_action(form, "Gerar post Markdown", self.run_blog_pipeline)
        layout.addWidget(group)
        self.post_result = QLabel("")
        self.post_result.setObjectName("Muted")
        self.post_result.setWordWrap(True)
        layout.addWidget(self.post_result)
        layout.addStretch(1)
        return page

    def _stories_page(self) -> QWidget:
        page, layout = self._page("Gerar Stories")
        group = QGroupBox("Brief")
        form = QFormLayout(group)
        self.story_topic = QLineEdit("RPV Federal")
        self.story_objective = QLineEdit("orientar com clareza")
        self.story_audience = QLineEdit("publico juridico")
        self.story_tone = QLineEdit("claro e responsavel")
        self.story_cta = QLineEdit("Fale com a Requisite")
        self.story_slides = QSpinBox()
        self.story_slides.setRange(1, 10)
        self.story_slides.setValue(3)
        self.story_template = QComboBox()
        self.story_template.addItems(["legal_clean", "metric_card"])
        self.story_brand = QComboBox()
        self._fill_brand_combo(self.story_brand)
        self.story_text_provider = QComboBox()
        self.story_text_provider.addItems(["mock", "custom", "openai", "anthropic", "gemini", "groq"])
        self.story_text_provider.setCurrentText(self.settings.default_text_provider)
        self.story_image_provider = QComboBox()
        self.story_image_provider.addItems(["local", "mock", "custom", "openai", "stability", "replicate"])
        self.story_image_provider.setCurrentText(self.settings.default_image_provider)
        self.story_use_brand = QCheckBox("usar manual de comunicacao visual")
        self.story_use_brand.setChecked(True)
        self.story_from_dino = QCheckBox("usar dados do Dino, se disponiveis")
        for label, widget in [
            ("Tema", self.story_topic),
            ("Objetivo", self.story_objective),
            ("Publico-alvo", self.story_audience),
            ("Tom de voz", self.story_tone),
            ("CTA", self.story_cta),
            ("Quantidade", self.story_slides),
            ("Template", self.story_template),
            ("Marca", self.story_brand),
            ("IA texto", self.story_text_provider),
            ("IA imagem", self.story_image_provider),
            ("Manual visual", self.story_use_brand),
            ("Dino", self.story_from_dino),
        ]:
            form.addRow(label, widget)
        self._add_action(form, "Gerar pacote de Stories", self.run_story_pipeline)
        layout.addWidget(group)
        self.story_result = QLabel("")
        self.story_result.setWordWrap(True)
        self.story_result.setObjectName("Muted")
        layout.addWidget(self.story_result)
        story_actions = QHBoxLayout()
        self._add_action(story_actions, "Abrir review.html", self.open_last_review)
        self._add_action(story_actions, "Abrir pasta da campanha", self.open_last_story_dir)
        story_actions.addStretch(1)
        layout.addLayout(story_actions)
        layout.addStretch(1)
        return page

    def _brands_page(self) -> QWidget:
        page, layout = self._page("Marcas")
        selector_group = QGroupBox("Perfil de marca")
        selector_form = QFormLayout(selector_group)
        self.brand_selector = QComboBox()
        self._fill_brand_combo(self.brand_selector)
        selector_form.addRow("Marca", self.brand_selector)
        self._add_action(selector_form, "Carregar perfil selecionado", self.load_selected_brand_profile)
        layout.addWidget(selector_group)

        actions = QHBoxLayout()
        self._add_action(actions, "Importar manual de comunicacao visual", self.import_brand_document)
        self._add_action(actions, "Salvar perfil editado", self.save_brand_profile_json)
        self._add_action(actions, "Validar perfil", self.validate_brand_profile_json)
        self._add_action(actions, "Usar esta marca como padrao", self.use_current_brand_default)
        actions.addStretch(1)
        layout.addLayout(actions)
        self.brand_status = QLabel("Nenhum BrandProfile carregado.")
        self.brand_status.setObjectName("Muted")
        self.brand_status.setWordWrap(True)
        layout.addWidget(self.brand_status)
        self.brand_profile_editor = QTextEdit()
        self.brand_profile_editor.setPlaceholderText("BrandProfile JSON aparecerá aqui para revisão e edição.")
        layout.addWidget(self.brand_profile_editor, 1)
        return page

    def _providers_page(self) -> QWidget:
        page, layout = self._page("IA / Providers")
        warning = QLabel("Custom provider usa formato OpenAI-compatible no MVP. Ao usar IA externa, conteudo do documento podera ser enviado ao provider configurado.")
        warning.setObjectName("Muted")
        warning.setWordWrap(True)
        layout.addWidget(warning)
        group = QGroupBox("Providers padrao e custom")
        form = QFormLayout(group)
        self.default_text_provider = QComboBox()
        self.default_text_provider.addItems(["mock", "custom", "openai", "anthropic", "gemini", "groq"])
        self.default_text_provider.setCurrentText(self.settings.default_text_provider)
        self.default_image_provider = QComboBox()
        self.default_image_provider.addItems(["local", "mock", "custom", "openai", "stability", "replicate"])
        self.default_image_provider.setCurrentText(self.settings.default_image_provider)
        self.default_vision_provider = QComboBox()
        self.default_vision_provider.addItems(["mock", "custom", "openai", "gemini", "groq"])
        self.default_vision_provider.setCurrentText(self.settings.default_vision_provider)
        self.provider_type = QComboBox()
        self.provider_type.addItems(["text", "image", "vision"])
        self.provider_model = QLineEdit("")
        self.provider_base_url = QLineEdit("")
        self.provider_endpoint = QLineEdit("")
        self.provider_api_key = QLineEdit("")
        self.provider_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.allow_external_brand_ai = QCheckBox("permitir enviar documentos de marca para IA externa")
        self.allow_external_brand_ai.setChecked(self.settings.allow_external_ai_for_brand_docs)
        for label, widget in [
            ("Texto padrao", self.default_text_provider),
            ("Imagem padrao", self.default_image_provider),
            ("Visao padrao", self.default_vision_provider),
            ("Tipo custom", self.provider_type),
            ("Model", self.provider_model),
            ("Base URL", self.provider_base_url),
            ("Endpoint", self.provider_endpoint),
            ("API key", self.provider_api_key),
            ("Documentos", self.allow_external_brand_ai),
        ]:
            form.addRow(label, widget)
        self._add_action(form, "Salvar configuracao", self.save_provider_settings)
        self._add_action(form, "Testar geracao curta", self.test_provider_settings)
        self.provider_type.currentTextChanged.connect(lambda _: self.load_provider_settings_form())
        self.load_provider_settings_form()
        layout.addWidget(group)
        self.provider_status = QLabel("Status: nao testado.")
        self.provider_status.setObjectName("Muted")
        layout.addWidget(self.provider_status)
        layout.addStretch(1)
        return page

    def _outputs_page(self) -> QWidget:
        page, layout = self._page("Saidas")
        self.outputs_label = QLabel("")
        self.outputs_label.setWordWrap(True)
        layout.addWidget(self.outputs_label)
        actions = QHBoxLayout()
        self._add_action(actions, "Atualizar lista", self.refresh_outputs)
        self._add_action(actions, "Abrir pasta de saida", self.open_output_root)
        actions.addStretch(1)
        layout.addLayout(actions)
        layout.addStretch(1)
        self.refresh_outputs()
        return page

    def _settings_page(self) -> QWidget:
        page, layout = self._page("Configuracoes")
        self.config_form = ConfigForm(self.settings)
        layout.addWidget(self.config_form)
        actions = QHBoxLayout()
        self._add_action(actions, "Salvar", self.save_settings)
        self._add_action(actions, "Testar configuracoes", self.run_environment_check)
        actions.addStretch(1)
        layout.addLayout(actions)
        layout.addStretch(1)
        return page

    def _add_action(self, layout: Any, text: str, callback: Any) -> QPushButton:
        button = QPushButton(text)
        button.clicked.connect(callback)
        self.action_buttons.append(button)
        if hasattr(layout, "addRow"):
            layout.addRow("", button)
        else:
            layout.addWidget(button)
        return button

    def _reload_services(self) -> tuple[BraveManager, EnvironmentService, PipelineService, OutputService]:
        self.settings = self.settings_service.load()
        return (
            BraveManager(self.settings),
            EnvironmentService(self.settings),
            PipelineService(self.settings),
            OutputService(self.settings),
        )

    def _brand_service(self) -> BrandService:
        self.settings = self.settings_service.load()
        return BrandService(self.settings)

    def _fill_brand_combo(self, combo: QComboBox) -> None:
        current = combo.currentData()
        combo.clear()
        combo.addItem("(sem marca)", "")
        try:
            from zero_insight.brand.cache import list_brand_profiles
            from zero_insight.brand import BrandProfile

            for path in list_brand_profiles():
                data = json.loads(path.read_text(encoding="utf-8"))
                profile = BrandProfile.from_dict(data)
                combo.addItem(profile.brand_name, str(path))
            preferred = str(current or self.settings.default_brand_profile_id or "")
            if preferred:
                self._select_combo_data(combo, preferred)
        except Exception:
            pass

    def _refresh_brand_selectors(self, selected_path: str | None = None) -> None:
        for attr in ("brand_selector", "story_brand", "post_brand"):
            combo = getattr(self, attr, None)
            if combo is not None:
                self._fill_brand_combo(combo)
                if selected_path:
                    self._select_combo_data(combo, selected_path)

    @staticmethod
    def _select_combo_data(combo: QComboBox, data: str) -> None:
        for index in range(combo.count()):
            if str(combo.itemData(index) or "") == str(data):
                combo.setCurrentIndex(index)
                return

    def _set_busy(self, busy: bool) -> None:
        self.state.busy = busy
        for button in self.action_buttons:
            button.setDisabled(busy)

    def _run_task(self, title: str, task: Any, on_result: Any | None = None) -> None:
        self._set_busy(True)
        self.progress_label.setText(title)
        thread = QThread(self)
        worker = Worker(task)
        worker.moveToThread(thread)
        worker.log.connect(self._append_log)
        worker.progress.connect(self._progress)
        worker.result.connect(lambda result: on_result(result) if on_result else None)
        worker.error.connect(self._show_worker_error)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(lambda: self._set_busy(False))
        thread.finished.connect(lambda: self.threads.remove(thread) if thread in self.threads else None)
        thread.finished.connect(thread.deleteLater)
        thread.started.connect(worker.run)
        self.threads.append(thread)
        thread.start()

    def _append_log(self, level: str, message: str) -> None:
        self.state.logs.append((level, message))
        self.logs.append(level, message)

    def _progress(self, value: int, message: str) -> None:
        self.progress.setValue(value)
        self.progress_label.setText(message)

    def _show_worker_error(self, message: str, details: str) -> None:
        self._append_log("ERROR", message)
        show_actionable_error(
            self,
            "Falha na operacao",
            "O que falhou: a tarefa nao foi concluida.\n"
            f"Possivel causa: {message}\n"
            "Acao recomendada: confira as configuracoes, Brave/CDP e logs.",
            details,
        )

    def refresh_dashboard(self) -> None:
        brave, _, _, _ = self._reload_services()
        status = brave.get_status()
        self.cards["brave"].set_status("OK" if status.installed else "ERROR", status.path or status.message)
        self.cards["cdp"].set_status("OK" if status.cdp_connected else "WARNING", status.message)
        self.cards["url"].set_status("OK" if self.settings.target_url else "NONE", self.settings.target_url)
        self.cards["api"].set_status("OK" if self.settings.groq_api_key else "ERROR", self.settings.masked_api_key())

    def run_environment_check(self) -> None:
        _, env, _, _ = self._reload_services()

        def task(on_log=None):
            if on_log:
                on_log("INFO", "Rodando checks de ambiente.")
            return env.run_checks()

        def done(results):
            self._clear_layout(self.env_results)
            for item in results:
                self.env_results.addWidget(StatusCard(item.name, item.status, f"{item.message}\nAcao: {item.action}"))
            self.refresh_dashboard()

        self._run_task("Verificando ambiente", task, done)

    def refresh_brave_status(self) -> None:
        brave, _, _, _ = self._reload_services()
        status = brave.get_status()
        self.brave_status.setText(
            f"Instalado: {status.installed}\nCaminho: {status.path or '-'}\nCDP: {status.message}"
        )
        self.refresh_dashboard()

    def install_brave(self) -> None:
        brave, _, _, _ = self._reload_services()

        def task(on_log=None):
            ok = brave.install_brave_with_winget(on_log=on_log)
            if not ok:
                if on_log:
                    on_log("WARN", "Abrindo pagina oficial do Brave para instalacao manual.")
                brave.open_brave_download_page()
            return ok

        self._run_task("Instalando Brave", task, lambda _: self.refresh_brave_status())

    def start_brave(self) -> None:
        brave, _, _, _ = self._reload_services()
        brave.start_brave_with_cdp(on_log=self._append_log)
        self.refresh_brave_status()

    def test_cdp(self) -> None:
        brave, _, _, _ = self._reload_services()
        ok, msg = brave.test_cdp_connection()
        self._append_log("SUCCESS" if ok else "WARN", msg)
        self.refresh_brave_status()

    def open_dino(self) -> None:
        brave, _, _, _ = self._reload_services()
        ok, msg = brave.open_url_in_cdp_brave()
        self._append_log("SUCCESS" if ok else "ERROR", msg)

    def run_blog_pipeline(self) -> None:
        self.save_settings(silent=True)
        _, _, pipeline, _ = self._reload_services()
        brand = self.post_brand.currentData() if self.post_validate_brand.isChecked() else None

        def task(on_log=None):
            return pipeline.run_blog(on_log=on_log, brand=brand)

        def done(result):
            ok, data = result
            self.state.last_blog_result = data if ok else None
            path = data.get("post_markdown", "") if data else ""
            self.post_result.setText(f"Post gerado: {path}" if ok else "Post nao gerado. Veja os logs.")
            self.cards["last_run"].set_status("OK" if ok else "ERROR", "Blog Markdown")
            self.cards["last_output"].set_status("OK" if path else "NONE", path)

        self._run_task("Gerando post", task, done)

    def run_story_pipeline(self) -> None:
        self.save_settings(silent=True)
        _, _, pipeline, _ = self._reload_services()
        from_dino = self.story_from_dino.isChecked()
        brief = StoryBrief(
            topic=self.story_topic.text().strip() or "RPV Federal",
            objective=self.story_objective.text().strip(),
            audience=self.story_audience.text().strip(),
            tone=self.story_tone.text().strip(),
            cta=self.story_cta.text().strip(),
            slides=self.story_slides.value(),
            template=self.story_template.currentText(),
            source="dino" if from_dino else "manual",
            brand_profile_path=(self.story_brand.currentData() if self.story_use_brand.isChecked() else None),
            ai_text_provider=self.story_text_provider.currentText(),
            ai_image_provider=self.story_image_provider.currentText(),
        )

        def task(on_log=None):
            return pipeline.run_stories(
                brief,
                from_dino=from_dino,
                on_log=on_log,
            )

        def done(result):
            ok, manifest = result
            self.state.last_story_manifest = manifest if manifest else None
            outputs = manifest.get("outputs", {}) if manifest else {}
            directory = outputs.get("directory", "")
            self.story_result.setText(f"Pacote gerado: {directory}" if ok else "Stories nao validados. Veja os logs.")
            self.cards["last_run"].set_status("OK" if ok else "ERROR", "Instagram Stories")
            self.cards["last_output"].set_status("OK" if directory else "NONE", directory)
            self.refresh_outputs()

        self._run_task("Gerando Stories", task, done)

    def save_settings(self, silent: bool = False) -> None:
        values = self.config_form.values()
        values["target_url"] = self.post_url.text().strip() or values["target_url"]
        self.settings = self.settings_service.update_from_form(self.settings, values)
        self.settings_service.save(self.settings)
        if not silent:
            self._append_log("SUCCESS", "Configuracoes salvas em .env.")
            self.refresh_dashboard()

    def import_brand_document(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar manual de comunicacao visual",
            "",
            "Documentos e imagens de marca (*.pdf *.docx *.png *.jpg *.jpeg *.webp)",
        )
        if not path:
            return
        default_name = Path(path).stem
        brand_name, ok = QInputDialog.getText(
            self,
            "Nome da marca",
            "Nome que sera usado para salvar o perfil:",
            text=default_name,
        )
        if not ok:
            return
        brand_name = brand_name.strip() or default_name
        service = self._brand_service()

        def task(on_log=None):
            return service.import_document(
                Path(path),
                brand_name=brand_name,
                use_external_ai=self.settings.allow_external_ai_for_brand_docs,
                on_log=on_log,
            )

        def done(result):
            profile, profile_path = result

            self.brand_profile_editor.setPlainText(json.dumps(profile.to_dict(), ensure_ascii=False, indent=2))
            self.brand_status.setText(f"Perfil gerado: {profile_path}\nStatus: {profile.status}")
            self._refresh_brand_selectors(str(profile_path))

        self._run_task("Importando manual de marca", task, done)

    def load_selected_brand_profile(self) -> None:
        current = self.brand_selector.currentData() if hasattr(self, "brand_selector") else None
        if not current:
            self.brand_status.setText("Selecione uma marca para carregar.")
            return
        try:
            from zero_insight.brand.cache import load_brand_profile

            profile = load_brand_profile(current)
            self.brand_profile_editor.setPlainText(json.dumps(profile.to_dict(), ensure_ascii=False, indent=2))
            self.brand_status.setText(f"Perfil carregado: {current}\nStatus: {profile.status}")
            self._select_combo_data(self.story_brand, str(current))
            self._select_combo_data(self.post_brand, str(current))
        except Exception as exc:
            show_actionable_error(self, "Erro ao carregar perfil", str(exc))

    def save_brand_profile_json(self) -> None:
        try:
            path = self._brand_service().save_profile_from_json(self.brand_profile_editor.toPlainText())
            self.brand_status.setText(f"Perfil salvo: {path}")
            self._refresh_brand_selectors(str(path))
        except Exception as exc:
            show_actionable_error(self, "Erro ao salvar perfil", f"JSON invalido ou incompleto: {exc}")

    def validate_brand_profile_json(self) -> None:
        try:
            import json
            from zero_insight.brand import BrandProfile, BrandValidator

            profile = BrandProfile.from_dict(json.loads(self.brand_profile_editor.toPlainText()))
            result = BrandValidator().validate_profile(profile)
            self.brand_status.setText(f"Validacao: {result['status']}\nAvisos: {', '.join(result['warnings']) or '-'}")
        except Exception as exc:
            show_actionable_error(self, "Erro ao validar perfil", str(exc))

    def use_current_brand_default(self) -> None:
        current = ""
        for attr in ("brand_selector", "story_brand", "post_brand"):
            combo = getattr(self, attr, None)
            if combo is not None and combo.currentData():
                current = str(combo.currentData())
                break
        if current:
            self.settings.default_brand_profile_id = str(current)
            self.settings_service.save(self.settings)
            self._refresh_brand_selectors(current)
            self.brand_status.setText(f"Marca padrao: {current}")
        else:
            self.brand_status.setText("Selecione uma marca antes de definir o padrao.")

    def save_provider_settings(self) -> None:
        kind = self.provider_type.currentText()
        providers = dict(self.settings.providers or {})
        providers.setdefault(kind, {})
        providers[kind]["custom"] = {
            "model": self.provider_model.text().strip(),
            "base_url": self.provider_base_url.text().strip(),
            "endpoint": self.provider_endpoint.text().strip(),
            "api_key_value": self.provider_api_key.text().strip(),
        }
        self.settings.providers = providers
        self.settings.default_text_provider = self.default_text_provider.currentText()
        self.settings.default_image_provider = self.default_image_provider.currentText()
        self.settings.default_vision_provider = self.default_vision_provider.currentText()
        self.settings.allow_external_ai_for_brand_docs = self.allow_external_brand_ai.isChecked()
        self.settings_service.save(self.settings)
        self.story_text_provider.setCurrentText(self.settings.default_text_provider)
        self.story_image_provider.setCurrentText(self.settings.default_image_provider)
        self.provider_status.setText("Status: configuracao salva. API key nao sera exibida em logs.")

    def load_provider_settings_form(self) -> None:
        kind = self.provider_type.currentText()
        providers = self.settings.providers or {}
        raw = {}
        if isinstance(providers, dict):
            raw = providers.get(kind, {}).get("custom", {}) or {}
        self.provider_model.setText(str(raw.get("model") or ""))
        self.provider_base_url.setText(str(raw.get("base_url") or ""))
        self.provider_endpoint.setText(str(raw.get("endpoint") or ""))
        api_key = raw.get("api_key_value")
        self.provider_api_key.setText("" if api_key == "***" else str(api_key or ""))

    def _selected_provider_config(self):
        from zero_insight.ai_providers import ProviderConfig

        kind = self.provider_type.currentText()
        selected = {
            "text": self.default_text_provider.currentText(),
            "image": self.default_image_provider.currentText(),
            "vision": self.default_vision_provider.currentText(),
        }[kind]
        if selected != "custom":
            config = ProviderConfig(kind, selected)
            if kind == "image" and selected == "local":
                config.model = self.settings.local_image_model_path
            return config
        return ProviderConfig(
            kind,
            selected,
            model=self.provider_model.text().strip(),
            base_url=self.provider_base_url.text().strip() or None,
            endpoint=self.provider_endpoint.text().strip() or None,
            api_key_value=self.provider_api_key.text().strip() or None,
        )

    def test_provider_settings(self) -> None:
        from zero_insight.ai_providers import create_image_provider, create_text_provider, create_vision_provider

        config = self._selected_provider_config()

        def task(on_log=None):
            if config.provider_type == "text":
                provider = create_text_provider(config)
                provider.generate_text("Responda apenas OK.")
                return True, f"{config.provider_type}:{provider.name} OK"
            if config.provider_type == "image":
                provider = create_image_provider(config)
                output = Path(".zeroinsight_appdata") / "cache" / "provider_test.png"
                provider.generate_image("Teste simples de integracao visual.", 512, 512, output)
                return True, f"{config.provider_type}:{provider.name} OK - {output}"
            provider = create_vision_provider(config)
            sample = Path(".zeroinsight_appdata") / "cache" / "provider_test.png"
            sample.parent.mkdir(parents=True, exist_ok=True)
            if not sample.exists():
                create_image_provider(None).generate_image("Amostra para teste de visao.", 512, 512, sample)
            provider.analyze_image(sample, "Responda apenas OK.")
            return True, f"{config.provider_type}:{provider.name} OK"

        def done(result):
            ok, msg = result
            self.provider_status.setText(("OK: " if ok else "Erro: ") + msg)

        self._run_task("Testando provider", task, done)

    def refresh_outputs(self) -> None:
        _, _, _, outputs = self._reload_services()
        posts = outputs.list_posts()[:5]
        campaigns = outputs.list_story_campaigns()[:5]
        text = ["Posts recentes:"]
        text.extend([f"- {p}" for p in posts] or ["- nenhum post encontrado"])
        text.append("\nCampanhas de Stories recentes:")
        text.extend([f"- {p}" for p in campaigns] or ["- nenhuma campanha encontrada"])
        self.outputs_label.setText("\n".join(text))

    def open_output_root(self) -> None:
        _, _, _, outputs = self._reload_services()
        root = Path(self.settings.output_dir).expanduser() if self.settings.output_dir else Path.cwd()
        self._open_path(outputs, root)

    def open_last_review(self) -> None:
        if not self.state.last_story_manifest:
            self._append_log("WARN", "Nenhum review.html recente nesta sessao.")
            return
        _, _, _, outputs = self._reload_services()
        review = self.state.last_story_manifest.get("outputs", {}).get("review")
        if review:
            self._open_path(outputs, Path(review))
        else:
            self._append_log("WARN", "A campanha recente nao tem review.html registrado.")

    def open_last_story_dir(self) -> None:
        if not self.state.last_story_manifest:
            self._append_log("WARN", "Nenhuma campanha recente nesta sessao.")
            return
        _, _, _, outputs = self._reload_services()
        directory = self.state.last_story_manifest.get("outputs", {}).get("directory")
        if directory:
            self._open_path(outputs, Path(directory))
        else:
            self._append_log("WARN", "A campanha recente nao tem pasta registrada.")

    def _open_path(self, outputs: OutputService, path: Path) -> None:
        try:
            if not path.exists():
                raise FileNotFoundError(f"Caminho nao encontrado: {path}")
            outputs.open_path(path)
        except Exception as exc:
            show_actionable_error(
                self,
                "Erro ao abrir caminho",
                f"Nao foi possivel abrir: {path}",
                str(exc),
            )

    @staticmethod
    def _clear_layout(layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
