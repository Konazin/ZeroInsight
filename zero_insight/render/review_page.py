from __future__ import annotations

import html
from pathlib import Path

from zero_insight.content import StoryBrief, StorySlide


def write_review_page(
    output_path: Path,
    brief: StoryBrief,
    slides: list[StorySlide],
    image_paths: list[Path],
    validation: dict[str, object],
) -> Path:
    cards = []
    for slide, image_path in zip(slides, image_paths, strict=False):
        cards.append(
            f"""
            <article class="card">
              <img src="{html.escape(image_path.name)}" alt="Story {slide.order}">
              <div>
                <h2>Story {slide.order}: {html.escape(slide.hook)}</h2>
                <p>{html.escape(slide.body)}</p>
                <strong>{html.escape(slide.cta)}</strong>
                <p class="notes">{html.escape("; ".join(slide.compliance_notes))}</p>
              </div>
            </article>
            """
        )

    page = f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Revisao Stories - {html.escape(brief.topic)}</title>
  <style>
    body {{ margin: 0; font-family: Arial, sans-serif; background: #f3f4f6; color: #111827; }}
    header {{ padding: 32px; background: #111827; color: white; }}
    main {{ max-width: 1100px; margin: 0 auto; padding: 28px; }}
    .card {{ display: grid; grid-template-columns: 220px 1fr; gap: 24px; margin-bottom: 24px; background: white; padding: 20px; border-radius: 8px; }}
    img {{ width: 220px; height: 391px; object-fit: cover; border-radius: 6px; }}
    .notes {{ color: #4b5563; }}
    code {{ background: #e5e7eb; padding: 2px 6px; border-radius: 4px; }}
  </style>
</head>
<body>
  <header>
    <h1>Pacote de Stories aguardando revisao</h1>
    <p>Tema: {html.escape(brief.topic)} | Template: <code>{html.escape(brief.template)}</code></p>
    <p>Status validacao: {html.escape(str(validation.get("ok")))}</p>
  </header>
  <main>
    {''.join(cards)}
  </main>
</body>
</html>
"""
    output_path.write_text(page, encoding="utf-8")
    return output_path
