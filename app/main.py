"""Studio Orot 앱 엔트리포인트."""

from __future__ import annotations

import asyncio
import sys

from app.bots.bot_factory import create_multi_bots, create_single_bot
from app.config.settings import settings


def _require_token(name: str, value: str | None) -> str:
    """토큰 누락 시 알기 쉬운 에러를 출력합니다."""
    if not value:
        raise RuntimeError(f"{name} 값이 비어 있습니다. .env 파일을 확인하세요.")
    return value


async def run_single_bot() -> None:
    """1개 봇으로 전체 워크플로우를 테스트합니다."""
    bot = create_single_bot()
    token = _require_token("TOKEN_DIRECTOR", settings.token_director)
    print("🚀 SINGLE_BOT_MODE=true: 단일 봇 테스트 모드로 실행합니다.")
    await bot.start(token)


async def run_multi_bots() -> None:
    """11개 봇을 동시에 실행합니다."""
    bots = create_multi_bots()

    token_map = {
        "director": settings.token_director,
        "analyst_health": settings.token_analyst_health,
        "analyst_food": settings.token_analyst_food,
        "analyst_living": settings.token_analyst_living,
        "creative_instagram": settings.token_creative_instagram,
        "creative_threads": settings.token_creative_threads,
        "creative_blog": settings.token_creative_blog,
        "creative_visual": settings.token_creative_visual,
        "marketer_tag": settings.token_marketer_tag,
        "marketer_tiktok": settings.token_marketer_tiktok,
        "marketer_strategy": settings.token_marketer_strategy,
    }

    for key, token in token_map.items():
        _require_token(f"TOKEN_{key.upper()}", token)

    print("🚀 SINGLE_BOT_MODE=false: 11개 멀티봇 모드로 실행합니다.")
    await asyncio.gather(
        *(bots[key].start(token_map[key]) for key in bots)
    )


async def main() -> None:
    """실행 모드에 따라 봇을 시작합니다."""
    if settings.single_bot_mode:
        await run_single_bot()
    else:
        await run_multi_bots()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 서버가 종료되었습니다.")
    except Exception as exc:
        print(f"❌ 실행 오류: {exc}", file=sys.stderr)
        raise
