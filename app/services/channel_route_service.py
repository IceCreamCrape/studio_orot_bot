"""Discord 채널 라우팅 설정 저장소.

명령어로 지정한 채널을 JSON 파일에 저장합니다.
Docker 재시작 후에도 유지되도록 기본 저장 위치는 /data/channel_routes.json 입니다.
"""

from __future__ import annotations

import json
from pathlib import Path

import discord


VALID_CATEGORIES = {"건기식", "식품", "주방"}
VALID_STEPS = {"input", "text", "short", "publish", "log", "dashboard", "meeting"}


class ChannelRouteService:
    """카테고리/단계별 Discord 채널 ID를 관리합니다."""

    def __init__(self, path: str = "/data/channel_routes.json") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: dict[str, dict[str, int]] = {}
        self.load()

    def load(self) -> None:
        """JSON 파일에서 라우팅 정보를 읽습니다."""
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
        """현재 라우팅 정보를 JSON 파일에 저장합니다."""
        self.path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def set_route(self, category: str, step: str, channel_id: int) -> None:
        """특정 카테고리/단계의 출력 채널을 저장합니다."""
        category = self.normalize_category(category)
        step = self.normalize_step(step)
        self._data.setdefault(category, {})
        self._data[category][step] = int(channel_id)
        self.save()

    def clear_category(self, category: str) -> None:
        """특정 카테고리의 라우팅 설정을 삭제합니다."""
        category = self.normalize_category(category)
        self._data.pop(category, None)
        self.save()

    def get_channel_id(self, category: str, step: str) -> int | None:
        """저장된 채널 ID를 반환합니다."""
        category = self.normalize_category(category)
        step = self.normalize_step(step)
        return self._data.get(category, {}).get(step)

    def get_routes(self) -> dict[str, dict[str, int]]:
        """전체 라우팅 설정을 반환합니다."""
        return self._data

    async def resolve_channel(
        self,
        guild: discord.Guild | None,
        fallback_channel: discord.abc.Messageable,
        category: str,
        step: str,
    ) -> discord.abc.Messageable:
        """저장된 채널이 있으면 그 채널을, 없으면 현재 채널을 반환합니다."""
        if guild is None:
            return fallback_channel

        channel_id = self.get_channel_id(category, step)
        if channel_id is None:
            return fallback_channel

        channel = guild.get_channel(channel_id)
        if channel is None:
            return fallback_channel

        return channel

    @staticmethod
    def normalize_category(category: str) -> str:
        """카테고리 별칭을 표준 이름으로 정리합니다."""
        aliases = {
            "health": "건기식",
            "healthy": "건기식",
            "건강": "건기식",
            "food": "식품",
            "kitchen": "주방",
            "living": "주방",
            "리빙": "주방",
        }
        value = aliases.get(category.strip(), category.strip())
        if value not in VALID_CATEGORIES:
            raise ValueError(f"카테고리는 {', '.join(sorted(VALID_CATEGORIES))} 중 하나여야 합니다.")
        return value

    @staticmethod
    def normalize_step(step: str) -> str:
        """단계 별칭을 표준 이름으로 정리합니다."""
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
            "대시보드": "dashboard",
            "회의실": "meeting",
        }
        value = aliases.get(step.strip(), step.strip())
        if value not in VALID_STEPS:
            raise ValueError(f"단계는 {', '.join(sorted(VALID_STEPS))} 중 하나여야 합니다.")
        return value


channel_route_service = ChannelRouteService()
