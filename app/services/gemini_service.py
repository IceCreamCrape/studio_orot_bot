"""Gemini 호출 서비스.

USE_MOCK_GEMINI=true면 실제 Gemini API 없이도 테스트할 수 있습니다.
Docker/Discord 연결을 먼저 확인할 때 유용합니다.
"""

from __future__ import annotations

import asyncio
from typing import Any

import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

from app.agents.persona_models import PERSONAS
from app.config.settings import settings


class GeminiService:
    """Gemini API 래퍼."""

    def __init__(self) -> None:
        self.mock_mode = settings.use_mock_gemini or not settings.google_api_key

        self.primary_model = "gemini-3.1-flash-lite-preview"
        self.fallback_models = [
            "gemini-2.5-pro",
            "gemini-2.5-flash",
            "gemini-2.0-flash",
        ]

        if not self.mock_mode:
            genai.configure(api_key=settings.google_api_key)

    async def generate(
        self,
        persona_key: str,
        prompt: str,
        image: Any | None = None,
    ) -> str:
        """페르소나에 맞는 텍스트를 생성합니다."""

        print("🔥 Gemini generate 호출됨", flush=True)
        print("🔥 mock_mode =", self.mock_mode, flush=True)
        print("🔥 api_key exists =", bool(settings.google_api_key), flush=True)
        print("🔥 persona_key =", persona_key, flush=True)

        persona = PERSONAS[persona_key]

        if self.mock_mode:
            return self._mock_response(persona.display_name, prompt)

        model_chain = [self.primary_model] + self.fallback_models
        last_error: Exception | None = None

        for model_name in model_chain:
            try:
                print(f"🚀 Gemini 모델 호출 시도: {model_name}", flush=True)
                return await asyncio.to_thread(
                    self._call_gemini,
                    model_name,
                    persona.system_instruction,
                    prompt,
                    image,
                )

            except google_exceptions.ResourceExhausted as exc:
                last_error = exc
                print(f"⚠️ 쿼터 초과: {model_name} → 다음 모델로 전환", flush=True)
                continue

            except google_exceptions.NotFound as exc:
                last_error = exc
                print(f"⚠️ 모델 없음/접근 불가: {model_name} → 다음 모델로 전환", flush=True)
                continue

            except google_exceptions.PermissionDenied as exc:
                last_error = exc
                print(f"⚠️ 권한 문제: {model_name} → 다음 모델로 전환", flush=True)
                continue

            except Exception as exc:
                last_error = exc
                print(f"❌ Gemini 오류: {model_name}: {exc}", flush=True)
                continue

        return (
            "❌ Gemini 호출 실패\n"
            "모든 모델 호출이 실패했습니다.\n\n"
            f"마지막 오류:\n{last_error}"
        )

    @staticmethod
    def _call_gemini(
        model_name: str,
        system_instruction: str,
        prompt: str,
        image: Any | None = None,
    ) -> str:
        """실제 Gemini API를 동기 호출합니다."""

        model = genai.GenerativeModel(
            model_name=model_name,
            system_instruction=system_instruction,
        )

        if image is not None:
            response = model.generate_content([image, prompt])
        else:
            response = model.generate_content(prompt)

        return getattr(response, "text", "") or "응답이 비어 있습니다."

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