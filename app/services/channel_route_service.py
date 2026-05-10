"""Discord 채널 라우팅 설정 저장소.

공통 라우팅을 지원합니다.

예:
{
  "공통": {
    "meeting": 123,
    "log": 456,
    "dashboard": 789
  },
  "건기식": {
    "input": 111,
    "text": 222,
    "short": 333,
    "publish": 444
  }
}

카테고리별 meeting/log/dashboard가 없으면 공통 채널을 자동으로 사용합니다.
"""

from __future__ import annotations

import json
from pathlib import Path

import discord


VALID_CATEGORIES = {"공통", "건기식", "식품", "주방", "개발"}
VALID_STEPS = {"input", "text", "short", "publish", "log", "dashboard", "meeting"}


class ChannelRouteService:
    """카테고리/단계별 Discord 채널 ID를 관리합니다."""

    def __init__(self, path: str = "/data/channel_routes.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, dict[str, int]] = {}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self._data = {}
            return

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            self._data = {
                str(category): {str(step): int(channel_id) for step, channel_id in steps.items()}
                for category, steps in raw.items()
            }
        except Exception:
            self._data = {}

    def save(self) -> None:
        self.path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def set_route(self, category: str, step: str, channel_id: int) -> None:
        category = self.normalize_category(category)
        step = self.normalize_step(step)

        self._data.setdefault(category, {})
        self._data[category][step] = int(channel_id)
        self.save()

    def clear_category(self, category: str) -> None:
        category = self.normalize_category(category)
        self._data.pop(category, None)
        self.save()

    def get_channel_id(self, category: str, step: str) -> int | None:
        """저장된 채널 ID를 반환합니다.

        meeting/log/dashboard는 카테고리별 설정이 없으면 공통 설정을 사용합니다.
        """
        category = self.normalize_category(category)
        step = self.normalize_step(step)

        direct = self._data.get(category, {}).get(step)
        if direct is not None:
            return direct

        if step in {"meeting", "log", "dashboard"}:
            return self._data.get("공통", {}).get(step)

        return None

    def get_routes(self) -> dict[str, dict[str, int]]:
        return self._data

    async def resolve_channel(
        self,
        guild: discord.Guild | None,
        fallback_channel: discord.abc.Messageable,
        category: str,
        step: str,
    ) -> discord.abc.Messageable:
        if guild is None:
            return fallback_channel

        channel_id = self.get_channel_id(category, step)
        if channel_id is None:
            return fallback_channel

        channel = guild.get_channel(channel_id)
        if channel is None:
            return fallback_channel

        return channel

    async def resolve_common_channel(
        self,
        guild: discord.Guild | None,
        fallback_channel: discord.abc.Messageable,
        step: str,
    ) -> discord.abc.Messageable:
        """공통 채널을 가져옵니다."""
        return await self.resolve_channel(guild, fallback_channel, "공통", step)

    @staticmethod
    def normalize_category(category: str) -> str:
        aliases = {
            "common": "공통",
            "global": "공통",
            "main": "공통",
            "system": "공통",
            "health": "건기식",
            "healthy": "건기식",
            "건강": "건기식",
            "food": "식품",
            "kitchen": "주방",
            "living": "주방",
            "리빙": "주방",
            "dev": "개발",
            "test": "개발",
        }
        value = aliases.get(category.strip(), category.strip())
        if value not in VALID_CATEGORIES:
            raise ValueError(f"카테고리는 {', '.join(sorted(VALID_CATEGORIES))} 중 하나여야 합니다.")
        return value

    @staticmethod
    def normalize_step(step: str) -> str:
        aliases = {
            "소싱": "input",
            "분석": "input",
            "입력": "input",
            "텍스트": "text",
            "카피": "text",
            "본문": "text",
            "숏폼": "short",
            "릴스": "short",
            "틱톡": "short",
            "송출": "publish",
            "발행": "publish",
            "최종": "publish",
            "로그": "log",
            "시스템로그": "log",
            "대시보드": "dashboard",
            "회의실": "meeting",
            "회의": "meeting",
        }
        value = aliases.get(step.strip(), step.strip())
        if value not in VALID_STEPS:
            raise ValueError(f"단계는 {', '.join(sorted(VALID_STEPS))} 중 하나여야 합니다.")
        return value


channel_route_service = ChannelRouteService()
