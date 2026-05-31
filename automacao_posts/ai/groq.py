from __future__ import annotations

import httpx

from automacao_posts.config import Settings


async def test_groq(settings: Settings) -> tuple[bool, str]:
    if not settings.groq_api_key:
        return False, "GROQ_API_KEY não configurada no .env"

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.post(
                settings.groq_endpoint,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {settings.groq_api_key}",
                },
                json={
                    "model": settings.groq_model,
                    "messages": [{"role": "user", "content": "Responda apenas: ok"}],
                    "max_tokens": 5,
                },
            )
        if res.is_success:
            return True, f"Groq OK — modelo {settings.groq_model}"
        return False, f"Groq erro {res.status_code}: {res.text[:200]}"
    except Exception as err:
        return False, str(err)
