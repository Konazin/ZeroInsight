from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from zero_insight.ai_providers.base import ProviderError, TextProvider
from zero_insight.ai_providers.config import ProviderConfig


class OpenAITextProvider(TextProvider):
    name = "openai"

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config
        self.config.api_key_env = self.config.api_key_env or "OPENAI_API_KEY"
        self.config.model = self.config.model or os.getenv("OPENAI_TEXT_MODEL", "gpt-5.4-mini")
        self.reasoning_model = os.getenv("OPENAI_REASONING_MODEL", self.config.model or "gpt-5.5")
        self.base_url = self.config.base_url or os.getenv("OPENAI_BASE_URL") or None
        self.last_manifest: dict[str, Any] = {}

    def _client(self):
        api_key = self.config.api_key_value or os.getenv(self.config.api_key_env or "OPENAI_API_KEY", "")
        if not api_key:
            raise ProviderError("OpenAI configurada, mas OPENAI_API_KEY nao foi encontrada.")
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ProviderError("Dependencia oficial 'openai' nao instalada. Rode pip install -r requirements.txt.") from exc
        kwargs: dict[str, Any] = {"api_key": api_key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return OpenAI(**kwargs)

    def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.4,
    ) -> str:
        content = self._responses_create(prompt, system_prompt, self.config.model, temperature)
        self._record_manifest("text", self.config.model)
        return content

    def generate_json(
        self,
        prompt: str,
        schema_hint: dict[str, Any] | None = None,
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        schema_instruction = ""
        if schema_hint:
            schema_instruction = "\nResponda JSON valido para este schema:\n" + json.dumps(schema_hint, ensure_ascii=False)
        raw = self.generate_text(
            prompt + schema_instruction + "\nResponda apenas JSON valido.",
            system_prompt=system_prompt,
            temperature=0.2,
        )
        try:
            return self._parse_json(raw)
        except ProviderError:
            fixed = self.generate_text(
                "Corrija a resposta abaixo para JSON valido, sem markdown e sem explicacoes:\n" + raw,
                system_prompt="Voce corrige JSON invalido. Responda somente JSON.",
                temperature=0.0,
            )
            return self._parse_json(fixed)

    def generate_structured(
        self,
        prompt: str,
        schema: dict[str, Any],
        system_prompt: str | None = None,
        model: str | None = None,
    ) -> dict[str, Any]:
        try:
            client = self._client()
            response = client.responses.create(
                model=model or self.config.model,
                input=self._input(prompt, system_prompt),
                text={
                    "format": {
                        "type": "json_schema",
                        "name": schema.get("title") or "ZeroInsightStructuredOutput",
                        "schema": schema,
                        "strict": True,
                    }
                },
            )
            self._record_manifest("structured", model or self.config.model)
            return self._parse_json(self._output_text(response))
        except Exception:
            return self.generate_json(prompt, schema_hint=schema, system_prompt=system_prompt)

    def extract_brand_profile(self, document_text: str, schema: dict[str, Any]) -> dict[str, Any]:
        return self.generate_structured(document_text, schema, system_prompt="Extraia BrandProfile. Nao invente dados ausentes.")

    def generate_story_script(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        return self.generate_structured(prompt, schema, system_prompt="Gere roteiro curto de Stories em JSON validado.")

    def generate_post_copy(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        return self.generate_structured(prompt, schema, system_prompt="Gere copy institucional sem promessas garantidas.")

    def generate_image_prompt(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        return self.generate_structured(prompt, schema, system_prompt="Gere prompts de imagem sem texto embutido.")

    def validate_compliance(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        return self.generate_structured(prompt, schema, system_prompt="Valide compliance com rigor e retorne JSON.", model=self.reasoning_model)

    def _responses_create(self, prompt: str, system_prompt: str | None, model: str, temperature: float) -> str:
        client = self._client()
        kwargs: dict[str, Any] = {"model": model, "input": self._input(prompt, system_prompt)}
        if temperature is not None:
            kwargs["temperature"] = temperature
        try:
            response = client.responses.create(**kwargs)
        except TypeError:
            kwargs.pop("temperature", None)
            response = client.responses.create(**kwargs)
        return self._output_text(response)

    @staticmethod
    def _input(prompt: str, system_prompt: str | None) -> list[dict[str, str]]:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

    @staticmethod
    def _output_text(response: Any) -> str:
        text = getattr(response, "output_text", None)
        if text:
            return str(text)
        data = response.model_dump() if hasattr(response, "model_dump") else response
        chunks: list[str] = []
        for item in data.get("output", []) if isinstance(data, dict) else []:
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"} and content.get("text"):
                    chunks.append(str(content["text"]))
        if chunks:
            return "\n".join(chunks)
        raise ProviderError("OpenAI retornou resposta sem texto utilizavel.")

    @staticmethod
    def _parse_json(text: str) -> dict[str, Any]:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                data = json.loads(text[start : end + 1])
            else:
                raise ProviderError("OpenAI retornou JSON invalido.") from exc
        if not isinstance(data, dict):
            raise ProviderError("OpenAI retornou JSON valido, mas fora do formato esperado.")
        return data

    def _record_manifest(self, task_type: str, model: str) -> None:
        self.last_manifest = {
            "ai_text_provider": "openai",
            "ai_text_model": model,
            "task_type": task_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
