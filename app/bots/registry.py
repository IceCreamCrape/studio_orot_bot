"""봇/역할/작업 상태 레지스트리.

bot_memory는 간단한 로컬 테스트용 메모리입니다.
서버 재시작 후 유지하려면 Redis나 DB로 바꾸면 됩니다.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class JobMemory:
    """채널 단위 작업 상태."""

    category: str
    platform: str
    trigger_word: str
    coupang_link: str
    topic: str
    image_available: bool = False
    steps: list[tuple[str, str]] = field(default_factory=list)

    def add_step(self, role: str, content: str) -> None:
        self.steps.append((role, content))

    def as_context(self) -> str:
        """이전 단계 결과를 하나의 프롬프트로 합칩니다."""
        lines = [
            f"카테고리: {self.category}",
            f"플랫폼: {self.platform}",
            f"댓글 유도 단어: {self.trigger_word}",
            f"쿠팡 링크: {self.coupang_link}",
            f"주제: {self.topic}",
            "",
            "이전 단계 결과:",
        ]
        for role, content in self.steps:
            lines.append(f"\n[{role}]\n{content}")
        return "\n".join(lines)


# 채널 ID별 작업 메모리
job_memory: dict[int, JobMemory] = {}


# 멀티봇 모드에서 실제 봇 ID를 저장합니다.
bot_ids: dict[str, int] = {}
