"""Gemini 호출 서비스.

USE_MOCK_GEMINI=true면 실제 Gemini API 없이도 테스트할 수 있습니다.
Docker/Discord 연결을 먼저 확인할 때 유용합니다.
"""

from __future__ import annotations

import asyncio
from typing import Any

import google.generativeai as genai

from app.agents.persona_models import PERSONAS
from app.config.settings import settings


class GeminiService:
    """Gemini API 래퍼.

    google-generativeai는 동기 호출 기반이므로 asyncio.to_thread로 감싸
    Discord 이벤트 루프가 멈추지 않도록 합니다.
    """

    def __init__(self) -> None:
        self.mock_mode = settings.use_mock_gemini or not settings.google_api_key
        if not self.mock_mode:
            genai.configure(api_key=settings.google_api_key)

    async def generate(
        self,
        persona_key: str,
        prompt: str,
        image: Any | None = None,
    ) -> str:
        """페르소나에 맞는 텍스트를 생성합니다."""
        persona = PERSONAS[persona_key]

        if self.mock_mode:
            return self._mock_response(persona.display_name, prompt)

        def _call() -> str:
            model = genai.GenerativeModel(
                model_name="gemini-2.5-pro",
                system_instruction=persona.system_instruction,
            )
            if image is not None:
                response = model.generate_content([image, prompt])
            else:
                response = model.generate_content(prompt)
            return getattr(response, "text", "") or "응답이 비어 있습니다."

        return await asyncio.to_thread(_call)

    @staticmethod
    def _mock_response(display_name: str, prompt: str) -> str:
        """API 없이 테스트하기 위한 가짜 응답."""
        preview = prompt.replace("\n", " ")[:180]
        return (
            f"[MOCK: {display_name}]\n"
            f"입력 요약: {preview}...\n\n"
            "1. 핵심 포인트: 상품의 시각적 매력과 실사용 장면을 중심으로 설득합니다.\n"
            "2. 타겟 포인트: 문제 상황을 먼저 보여주고 해결책으로 제품을 제안합니다.\n"
            "3. 콘텐츠 포인트: 댓글 유도형 CTA를 사용해 DM 전환 흐름을 만듭니다."
        )


gemini_service = GeminiService()
