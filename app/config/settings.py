"""환경변수 로더.

이 파일은 프로젝트 전체에서 사용하는 설정을 한곳에 모아둡니다.
.env 값을 직접 여러 파일에서 읽으면 관리가 어려워지므로 Settings 객체로 통일합니다.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


def _bool_env(name: str, default: bool = False) -> bool:
    """문자열 환경변수를 bool로 변환합니다."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class Settings:
    """앱 전체 설정."""

    single_bot_mode: bool
    use_mock_gemini: bool
    enable_make_webhook: bool

    google_api_key: str | None
    make_webhook_url: str | None

    token_director: str | None
    token_analyst_health: str | None
    token_analyst_food: str | None
    token_analyst_living: str | None
    token_creative_instagram: str | None
    token_creative_threads: str | None
    token_creative_blog: str | None
    token_creative_visual: str | None
    token_marketer_tag: str | None
    token_marketer_tiktok: str | None
    token_marketer_strategy: str | None

    @classmethod
    def load(cls) -> "Settings":
        return cls(
            single_bot_mode=_bool_env("SINGLE_BOT_MODE", True),
            use_mock_gemini=_bool_env("USE_MOCK_GEMINI", True),
            enable_make_webhook=_bool_env("ENABLE_MAKE_WEBHOOK", False),
            google_api_key=os.getenv("GOOGLE_API_KEY"),
            make_webhook_url=os.getenv("MAKE_WEBHOOK_URL"),
            token_director=os.getenv("TOKEN_DIRECTOR"),
            token_analyst_health=os.getenv("TOKEN_ANALYST_HEALTH"),
            token_analyst_food=os.getenv("TOKEN_ANALYST_FOOD"),
            token_analyst_living=os.getenv("TOKEN_ANALYST_LIVING"),
            token_creative_instagram=os.getenv("TOKEN_CREATIVE_INSTAGRAM"),
            token_creative_threads=os.getenv("TOKEN_CREATIVE_THREADS"),
            token_creative_blog=os.getenv("TOKEN_CREATIVE_BLOG"),
            token_creative_visual=os.getenv("TOKEN_CREATIVE_VISUAL"),
            token_marketer_tag=os.getenv("TOKEN_MARKETER_TAG"),
            token_marketer_tiktok=os.getenv("TOKEN_MARKETER_TIKTOK"),
            token_marketer_strategy=os.getenv("TOKEN_MARKETER_STRATEGY"),
        )


settings = Settings.load()
