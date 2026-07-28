from __future__ import annotations

import asyncio
import inspect
import os
import shutil
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from zero_insight.ai_providers import (
    ProviderConfig,
    create_image_provider,
    list_ai_providers,
    provider_config_from_settings,
)
from zero_insight.ai_providers.base import TextProvider
from zero_insight.browser.extract import _parse_br_number
from zero_insight.config import Settings
from zero_insight.content import StoryBrief, StorySlide, plan_story_script_with_provider
from zero_insight.image.prompt_builder import build_full_composition_prompt
from zero_insight.pipeline.story_runner import _create_output_dir, run_story_pipeline
from zero_insight.server.routes.settings import (
    _public_settings,
    _restore_masked_values,
)


def make_brief(**overrides) -> StoryBrief:
    values = {
        "topic": "RPV Federal",
        "objective": "orientar",
        "audience": "público jurídico",
        "tone": "claro",
        "cta": "Fale conosco",
        "slides": 1,
        "template": "legal_clean",
    }
    values.update(overrides)
    return StoryBrief(**values)


class FakeStoryProvider(TextProvider):
    name = "fake"

    def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.4,
    ) -> str:
        raise AssertionError("generate_json should be used")

    def generate_json(self, prompt, schema_hint=None, system_prompt=None):
        count = 2
        return {
            "slides": [
                {
                    "order": index,
                    "hook": f"Hook {index}",
                    "body": f"Body {index}",
                    "cta": "Contato",
                    "visual_idea": f"Visual {index}",
                    "image_prompt": f"Imagem {index}",
                    "compliance_notes": ["Revisar"],
                }
                for index in range(1, count + 1)
            ]
        }


class LogicRegressionTests(unittest.TestCase):
    def test_brazilian_number_parser_handles_millions(self) -> None:
        self.assertEqual(_parse_br_number("1.234"), 1234.0)
        self.assertEqual(_parse_br_number("1.234.567"), 1234567.0)
        self.assertEqual(_parse_br_number("12.345.678"), 12345678.0)
        self.assertEqual(_parse_br_number("1.234.567,89"), 1234567.89)

    def test_public_settings_masks_and_restores_nested_provider_secret(self) -> None:
        settings = Settings(
            providers={
                "text": {
                    "custom": {
                        "model": "modelo",
                        "api_key_value": "segredo-real",
                    }
                }
            }
        )
        public = _public_settings(settings)
        self.assertEqual(
            public["providers"]["text"]["custom"]["api_key_value"],
            "****",
        )
        restored = _restore_masked_values(public["providers"], settings.providers)
        self.assertEqual(
            restored["text"]["custom"]["api_key_value"],
            "segredo-real",
        )

    def test_all_advertised_image_providers_accept_logo_keyword(self) -> None:
        for name in list_ai_providers()["image"]:
            provider = create_image_provider(ProviderConfig("image", name))
            parameters = inspect.signature(provider.generate_image).parameters
            self.assertIn("logo_path", parameters, name)

    def test_registry_does_not_advertise_unimplemented_providers(self) -> None:
        available = list_ai_providers()
        self.assertNotIn("anthropic", available["text"])
        self.assertNotIn("gemini", available["vision"])
        self.assertNotIn("stability", available["image"])
        self.assertNotIn("replicate", available["image"])

    def test_groq_configuration_uses_central_settings(self) -> None:
        settings = Settings(
            groq_api_key="gsk-test",
            groq_endpoint="https://example.test/chat/completions",
            groq_model="modelo-texto",
        )
        config = provider_config_from_settings(settings, "text", "groq")
        self.assertEqual(config.api_key_value, "gsk-test")
        self.assertEqual(config.endpoint, settings.groq_endpoint)
        self.assertEqual(config.model, "modelo-texto")

    def test_selected_text_provider_builds_validated_script(self) -> None:
        brief = make_brief(slides=2)
        slides = plan_story_script_with_provider(brief, FakeStoryProvider())
        self.assertEqual([slide.order for slide in slides], [1, 2])
        self.assertEqual(slides[1].hook, "Hook 2")

    def test_assisted_customization_keeps_mandatory_slide_content(self) -> None:
        brief = make_brief(
            image_style_instructions=(
                "Use estilo editorial. O título deve ser [Título do story]."
            )
        )
        slide = StorySlide(
            order=1,
            hook="Título obrigatório",
            body="Corpo obrigatório",
            cta="CTA obrigatório",
            visual_idea="Fundo limpo",
            image_prompt="Fundo limpo",
        )
        prompt = build_full_composition_prompt(brief, slide)
        self.assertIn("Título obrigatório", prompt)
        self.assertIn("Corpo obrigatório", prompt)
        self.assertIn("Use estilo editorial", prompt)
        self.assertIn("Replace any bracketed", prompt)


class PipelineRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runtime = Path("tests") / f".runtime_{os.getpid()}"
        self.runtime.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.runtime, ignore_errors=True)

    def test_explicit_local_provider_generates_successfully(self) -> None:
        settings = Settings(
            output_dir=str(self.runtime),
            default_text_provider="mock",
            default_image_provider="local",
            story_width=540,
            story_height=960,
        )
        ok, manifest = asyncio.run(
            run_story_pipeline(
                settings,
                make_brief(ai_image_provider="local", ai_text_provider="mock"),
            )
        )
        self.assertTrue(ok, manifest)
        self.assertEqual(len(manifest["outputs"]["images"]), 1)
        self.assertEqual(
            manifest["image_prompts"][0]["prompt_mode"],
            "assisted",
        )
        self.assertTrue(manifest["image_prompts"][0]["prompt_sent"])

    def test_concurrent_campaign_names_get_distinct_directories(self) -> None:
        settings = Settings(output_dir=str(self.runtime))
        created_at = datetime(2026, 7, 28, 12, 30, tzinfo=timezone.utc)
        first = _create_output_dir(settings, created_at, "campanha")
        second = _create_output_dir(settings, created_at, "campanha")
        self.assertNotEqual(first, second)
        self.assertTrue(first.is_dir())
        self.assertTrue(second.is_dir())

    def test_pipeline_uses_selected_text_provider(self) -> None:
        settings = Settings(
            output_dir=str(self.runtime),
            default_text_provider="mock",
            default_image_provider="mock",
            story_width=540,
            story_height=960,
        )
        with patch(
            "zero_insight.pipeline.story_runner.create_text_provider",
            return_value=FakeStoryProvider(),
        ):
            ok, manifest = asyncio.run(
                run_story_pipeline(
                    settings,
                    make_brief(
                        slides=2,
                        ai_text_provider="custom",
                        ai_image_provider="mock",
                    ),
                )
            )
        self.assertTrue(ok, manifest)
        self.assertEqual(manifest["slides"][0]["hook"], "Hook 1")
        self.assertEqual(manifest["ai_providers_used"]["text"], "custom")
        self.assertEqual(
            manifest["ai_text_metadata"]["ai_text_provider"],
            "fake",
        )

    def test_legacy_unimplemented_default_image_provider_falls_back_local(self) -> None:
        settings = Settings(
            output_dir=str(self.runtime),
            default_text_provider="mock",
            default_image_provider="stability",
            story_width=540,
            story_height=960,
        )
        ok, manifest = asyncio.run(run_story_pipeline(settings, make_brief()))
        self.assertTrue(ok, manifest)
        self.assertEqual(manifest["ai_providers_used"]["image"], "local")
        self.assertEqual(
            manifest["ai_providers_used"]["image_requested"],
            "stability",
        )
        self.assertEqual(manifest["ai_providers_used"]["image_fallback"], "local")

    def test_manual_prompt_with_forbidden_claim_is_blocked(self) -> None:
        settings = Settings(
            output_dir=str(self.runtime),
            default_text_provider="mock",
            default_image_provider="mock",
            story_width=540,
            story_height=960,
        )
        ok, manifest = asyncio.run(
            run_story_pipeline(
                settings,
                make_brief(
                    ai_image_provider="mock",
                    ai_text_provider="mock",
                    custom_image_prompt="Resultado 100% aprovado e sem risco.",
                ),
            )
        )
        self.assertFalse(ok)
        self.assertEqual(manifest["status"], "FAILED")
        self.assertIn("compliance", manifest["validation"]["errors"][0].lower())

    def test_manual_prompt_uses_mock_path_without_being_ignored(self) -> None:
        settings = Settings(
            output_dir=str(self.runtime),
            default_text_provider="mock",
            default_image_provider="mock",
            story_width=540,
            story_height=960,
        )
        prompt = "Composição institucional abstrata em azul."
        ok, manifest = asyncio.run(
            run_story_pipeline(
                settings,
                make_brief(
                    ai_image_provider="mock",
                    ai_text_provider="mock",
                    custom_image_prompt=prompt,
                ),
            )
        )
        self.assertTrue(ok, manifest)
        self.assertEqual(manifest["image_prompts"][0]["prompt_mode"], "manual")
        self.assertEqual(manifest["image_prompts"][0]["prompt_sent"], prompt)


if __name__ == "__main__":
    unittest.main()
