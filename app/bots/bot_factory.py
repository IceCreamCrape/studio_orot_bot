"""Discord 봇 생성 및 이벤트 등록.

테스트 편의성을 위해 SINGLE_BOT_MODE와 MULTI_BOT_MODE를 모두 지원합니다.
"""

from __future__ import annotations

import discord
from discord.ext import commands

from app.bots.registry import JobMemory, bot_ids, job_memory
from app.bots.workflow import run_full_workflow
from app.config.settings import settings
from app.utils.image_utils import read_first_image


def build_intents() -> discord.Intents:
    """봇이 사용할 Discord Intents."""
    intents = discord.Intents.default()
    # 접두사 명령어와 멘션 릴레이를 사용하려면 Developer Portal에서도 켜야 합니다.
    intents.message_content = True
    return intents


def create_bot(role_key: str, command_prefix: str = "!") -> commands.Bot:
    """공통 설정으로 Discord Bot 객체를 생성합니다."""
    bot = commands.Bot(command_prefix=command_prefix, intents=build_intents())

    @bot.event
    async def on_ready() -> None:
        if bot.user:
            bot_ids[role_key] = bot.user.id
            print(f"✅ {role_key} ready: {bot.user} ({bot.user.id})")

    return bot


def register_single_bot_commands(bot: commands.Bot) -> None:
    """1개 봇으로 전체 워크플로우를 테스트하는 명령어를 등록합니다."""

    @bot.command(name="상태")
    async def status(ctx: commands.Context) -> None:
        """봇 상태 확인."""
        await ctx.send(
            "✅ STUDIO OROT 테스트 봇 온라인\n"
            f"- SINGLE_BOT_MODE: {settings.single_bot_mode}\n"
            f"- USE_MOCK_GEMINI: {settings.use_mock_gemini}\n"
            f"- ENABLE_MAKE_WEBHOOK: {settings.enable_make_webhook}"
        )

    @bot.command(name="테스트기획")
    async def test_planning(
        ctx: commands.Context,
        category: str,
        platform: str,
        trigger_word: str,
        coupang_link: str,
        *,
        topic: str,
    ) -> None:
        """이미지 없이 전체 워크플로우를 테스트합니다.

        예:
        !테스트기획 리빙 인스타 수납 https://link.coupang.com/test 좁은 원룸에 어울리는 베이지 수납함
        """
        memory = JobMemory(
            category=category,
            platform=platform,
            trigger_word=trigger_word,
            coupang_link=coupang_link,
            topic=topic,
            image_available=False,
        )
        job_memory[ctx.channel.id] = memory

        await ctx.send(
            "🧪 이미지 없는 테스트 기획을 시작합니다.\n"
            "Gemini mock 모드라면 실제 API 없이 샘플 응답이 출력됩니다."
        )
        await run_full_workflow(ctx.channel, memory, image=None)

    @bot.command(name="기획시작")
    async def start_planning(
        ctx: commands.Context,
        category: str,
        platform: str,
        trigger_word: str,
        coupang_link: str,
        *,
        topic: str,
    ) -> None:
        """이미지를 첨부해서 전체 워크플로우를 실행합니다.

        예:
        !기획시작 리빙 인스타 수납 https://link.coupang.com/test 좁은 원룸에 어울리는 베이지 수납함
        """
        image = await read_first_image(ctx.message)
        if image is None:
            await ctx.send(
                "⚠️ 이미지가 없어서 이미지 분석 없이 진행합니다.\n"
                "이미지 테스트가 필요하면 상품 사진을 첨부한 뒤 같은 명령어를 입력하세요."
            )

        memory = JobMemory(
            category=category,
            platform=platform,
            trigger_word=trigger_word,
            coupang_link=coupang_link,
            topic=topic,
            image_available=image is not None,
        )
        job_memory[ctx.channel.id] = memory

        await ctx.send(
            f"📢 신규 오더 접수\n"
            f"- 카테고리: {category}\n"
            f"- 플랫폼: {platform}\n"
            f"- 댓글 단어: {trigger_word}\n"
            f"- 주제: {topic}"
        )
        await run_full_workflow(ctx.channel, memory, image=image)


def create_single_bot() -> commands.Bot:
    """로컬 테스트용 단일 봇."""
    bot = create_bot("director", command_prefix="!")
    register_single_bot_commands(bot)
    return bot


def create_multi_bots() -> dict[str, commands.Bot]:
    """11개 봇 객체를 생성합니다.

    주의:
    이 모드는 11개의 Discord Bot Token이 모두 필요합니다.
    현재 코드는 안정적인 테스트를 위해 명령 시작은 director_bot에서 받고,
    실제 처리 흐름은 단일 워크플로우 함수를 공유합니다.
    추후 멘션 릴레이형으로 확장하기 쉽게 역할별 객체를 분리해둔 구조입니다.
    """
    bots = {
        "director": create_bot("director", "!"),
        "analyst_health": create_bot("analyst_health", "?"),
        "analyst_food": create_bot("analyst_food", "?"),
        "analyst_living": create_bot("analyst_living", "?"),
        "creative_instagram": create_bot("creative_instagram", "^"),
        "creative_threads": create_bot("creative_threads", "^"),
        "creative_blog": create_bot("creative_blog", "^"),
        "creative_visual": create_bot("creative_visual", "^"),
        "marketer_tag": create_bot("marketer_tag", "~"),
        "marketer_tiktok": create_bot("marketer_tiktok", "~"),
        "marketer_strategy": create_bot("marketer_strategy", "~"),
    }

    # 실제 테스트 명령은 director bot에만 등록합니다.
    register_single_bot_commands(bots["director"])
    return bots
