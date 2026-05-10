"""Make.com Webhook 전송 서비스.

기본값은 비활성화입니다.
ENABLE_MAKE_WEBHOOK=false이면 실제 전송하지 않고 payload preview만 반환합니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import aiohttp

from app.config.settings import settings


@dataclass
class WebhookResult:
    """Webhook 실행 결과."""

    ok: bool
    message: str
    payload: dict[str, Any]


class WebhookService:
    """Make.com Webhook 전송 담당."""

    async def send_to_make(self, payload: dict[str, Any]) -> WebhookResult:
        """Make.com으로 payload를 전송하거나, 테스트 모드에서는 preview만 반환합니다."""

        # 테스트 모드: 실제 HTTP 요청을 하지 않습니다.
        if not settings.enable_make_webhook:
            return WebhookResult(
                ok=True,
                message="테스트 모드입니다. Make.com으로 실제 전송하지 않았습니다.",
                payload=payload,
            )

        if not settings.make_webhook_url:
            return WebhookResult(
                ok=False,
                message="MAKE_WEBHOOK_URL이 설정되어 있지 않습니다.",
                payload=payload,
            )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(settings.make_webhook_url, json=payload, timeout=30) as response:
                    text = await response.text()
                    if 200 <= response.status < 300:
                        return WebhookResult(True, f"Make.com 전송 성공: HTTP {response.status}", payload)
                    return WebhookResult(False, f"Make.com 전송 실패: HTTP {response.status} / {text}", payload)
        except Exception as exc:
            return WebhookResult(False, f"Make.com 전송 중 오류: {exc}", payload)


webhook_service = WebhookService()
