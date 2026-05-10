from __future__ import annotations

import base64
from pathlib import Path

import google.generativeai as genai

from app.config.settings import settings


class GeminiImageService:
    """Gemini 이미지 생성 서비스."""

    def __init__(self) -> None:
        self.enabled = bool(settings.google_api_key)

        if self.enabled:
            genai.configure(api_key=settings.google_api_key)

        self.model_name = "gemini-3.1-flash-image-preview"

    def generate_image(
        self,
        prompt: str,
        filename: str = "generated_image.png",
    ) -> Path | None:
        """프롬프트 기반 이미지 생성."""

        if not self.enabled:
            return None

        try:
            model = genai.GenerativeModel(self.model_name)

            response = model.generate_content(
                prompt,
                generation_config={
                    "response_modalities": ["TEXT", "IMAGE"]
                },
            )

            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    image_data = part.inline_data.data

                    output_path = Path("/tmp") / filename
                    output_path.write_bytes(image_data)

                    return output_path

        except Exception as exc:
            print(f"❌ Gemini 이미지 생성 실패: {exc}", flush=True)

        return None


gemini_image_service = GeminiImageService()