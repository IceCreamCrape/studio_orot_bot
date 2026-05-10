"""Discord 봇 생성 및 Slash Command 등록.

명령어 구조:
- /admin : 관리/설정
- /single : 단일 디렉터 봇 테스트
- /multi : 11개 멀티봇 운영 상태/안내
"""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from app.bots.registry import JobMemory, bot_ids, job_memory
from app.bots.workflow import run_full_workflow
from app.config.settings import settings
from app.services.channel_route_service import channel_route_service
from app.services.gemini_service import gemini_service


def build_intents() -> discord.Intents:
    """봇이 사용할 Discord Intents."""
    intents = discord.Intents.default()
    intents.message_content = True
    return intents


def create_bot(role_key: str, command_prefix: str = "!") -> commands.Bot:
    """공통 설정으로 Discord Bot 객체를 생성합니다."""
    bot = commands.Bot(command_prefix=command_prefix, intents=build_intents())

    @bot.event
    async def on_ready() -> None:
        if bot.user:
            bot_ids[role_key] = bot.user.id

            try:
                synced = await bot.tree.sync()
                print(f"✅ slash commands synced for {role_key}: {len(synced)}개", flush=True)
            except Exception as exc:
                print(f"❌ slash command sync failed for {role_key}: {exc}", flush=True)

            print(f"✅ {role_key} ready: {bot.user} ({bot.user.id})", flush=True)

    return bot


def _is_manager_interaction(interaction: discord.Interaction) -> bool:
    """슬래시 명령어용 관리자 권한 확인."""
    if interaction.guild is None:
        return True

    permissions = interaction.user.guild_permissions
    return permissions.manage_guild or permissions.administrator


async def _reject_if_not_manager(interaction: discord.Interaction) -> bool:
    """관리자가 아니면 거부 메시지를 보내고 True를 반환합니다."""
    if _is_manager_interaction(interaction):
        return False

    await interaction.response.send_message(
        "❌ 이 명령어는 서버 관리 권한이 필요합니다.",
        ephemeral=True,
    )
    return True


async def _send_long_response(
    interaction: discord.Interaction,
    content: str,
    ephemeral: bool = True,
) -> None:
    """Discord 메시지 길이 제한을 고려해 응답합니다."""
    if len(content) <= 1900:
        if interaction.response.is_done():
            await interaction.followup.send(content, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(content, ephemeral=ephemeral)
        return

    chunks = [content[i : i + 1900] for i in range(0, len(content), 1900)]

    if not interaction.response.is_done():
        await interaction.response.send_message(chunks[0], ephemeral=ephemeral)
        chunks = chunks[1:]

    for chunk in chunks:
        await interaction.followup.send(chunk, ephemeral=ephemeral)


def _format_routes(interaction: discord.Interaction) -> str:
    """채널 라우팅 목록을 문자열로 정리합니다."""
    routes = channel_route_service.get_routes()

    if not routes:
        return (
            "📭 저장된 채널 설정이 없습니다.\n"
            "예: `/admin 채널설정 category:주방 step:input channel:#개발-소싱-input`"
        )

    lines = ["🗺️ **현재 채널 라우팅 설정**"]

    for category, steps in routes.items():
        lines.append(f"\n**[{category}]**")
        for step, channel_id in steps.items():
            channel = interaction.guild.get_channel(channel_id) if interaction.guild else None
            channel_text = channel.mention if channel else f"`{channel_id}`"
            lines.append(f"- `{step}` → {channel_text}")

    return "\n".join(lines)


CATEGORY_CHOICES = [
    app_commands.Choice(name="건기식", value="건기식"),
    app_commands.Choice(name="식품", value="식품"),
    app_commands.Choice(name="주방", value="주방"),
    app_commands.Choice(name="개발", value="개발"),
]

STEP_CHOICES = [
    app_commands.Choice(name="input / 소싱 분석", value="input"),
    app_commands.Choice(name="text / 텍스트", value="text"),
    app_commands.Choice(name="short / 숏폼", value="short"),
    app_commands.Choice(name="publish / 송출", value="publish"),
    app_commands.Choice(name="log / 시스템 로그", value="log"),
    app_commands.Choice(name="dashboard / 대시보드", value="dashboard"),
    app_commands.Choice(name="meeting / 회의실", value="meeting"),
]

PLATFORM_CHOICES = [
    app_commands.Choice(name="인스타", value="인스타"),
    app_commands.Choice(name="쓰레드", value="쓰레드"),
    app_commands.Choice(name="블로그", value="블로그"),
    app_commands.Choice(name="틱톡", value="틱톡"),
    app_commands.Choice(name="릴스", value="릴스"),
    app_commands.Choice(name="숏폼", value="숏폼"),
]


class AdminCommands(app_commands.Group):
    """관리/설정용 슬래시 명령어 그룹."""

    def __init__(self) -> None:
        super().__init__(
            name="admin",
            description="스튜디오 오롯 봇 관리 명령어",
        )

    @app_commands.command(name="상태", description="봇 실행 상태와 환경 설정을 확인합니다.")
    async def status(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "✅ STUDIO OROT 봇 온라인\n"
            f"- SINGLE_BOT_MODE: `{settings.single_bot_mode}`\n"
            f"- USE_MOCK_GEMINI: `{settings.use_mock_gemini}`\n"
            f"- ENABLE_MAKE_WEBHOOK: `{settings.enable_make_webhook}`",
            ephemeral=True,
        )

    @app_commands.command(name="gemini테스트", description="Gemini API 연결을 테스트합니다.")
    async def gemini_test(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            response = await gemini_service.generate(
                persona_key="director",
                prompt="현재 Gemini 연결 상태를 한 줄로 설명해주세요.",
            )
            await interaction.followup.send(
                f"✅ Gemini 테스트 완료\n\n응답:\n{response}",
                ephemeral=True,
            )
        except Exception as exc:
            await interaction.followup.send(
                f"❌ Gemini 연결 실패\n```{exc}```",
                ephemeral=True,
            )

    @app_commands.command(name="채널목록", description="저장된 채널 라우팅 목록을 확인합니다.")
    async def list_channel_routes(self, interaction: discord.Interaction) -> None:
        await _send_long_response(interaction, _format_routes(interaction), ephemeral=True)

    @app_commands.command(name="채널설정", description="카테고리/단계별 출력 채널을 지정합니다.")
    @app_commands.describe(category="카테고리", step="작업 단계", channel="결과를 보낼 채널")
    @app_commands.choices(category=CATEGORY_CHOICES, step=STEP_CHOICES)
    async def set_channel_route(
        self,
        interaction: discord.Interaction,
        category: app_commands.Choice[str],
        step: app_commands.Choice[str],
        channel: discord.TextChannel,
    ) -> None:
        if await _reject_if_not_manager(interaction):
            return

        try:
            normalized_category = channel_route_service.normalize_category(category.value)
            normalized_step = channel_route_service.normalize_step(step.value)

            channel_route_service.set_route(normalized_category, normalized_step, channel.id)

            await interaction.response.send_message(
                "✅ 채널 설정 완료\n"
                f"- 카테고리: `{normalized_category}`\n"
                f"- 단계: `{normalized_step}`\n"
                f"- 채널: {channel.mention}\n"
                f"- 채널 ID: `{channel.id}`",
                ephemeral=True,
            )
        except Exception as exc:
            await interaction.response.send_message(
                f"❌ 채널 설정 실패\n```{exc}```",
                ephemeral=True,
            )

    @app_commands.command(name="현재채널설정", description="현재 채널을 카테고리/단계 출력 채널로 저장합니다.")
    @app_commands.describe(category="카테고리", step="작업 단계")
    @app_commands.choices(category=CATEGORY_CHOICES, step=STEP_CHOICES)
    async def set_current_channel_route(
        self,
        interaction: discord.Interaction,
        category: app_commands.Choice[str],
        step: app_commands.Choice[str],
    ) -> None:
        if await _reject_if_not_manager(interaction):
            return

        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message(
                "❌ 텍스트 채널에서만 사용할 수 있습니다.",
                ephemeral=True,
            )
            return

        try:
            normalized_category = channel_route_service.normalize_category(category.value)
            normalized_step = channel_route_service.normalize_step(step.value)

            channel_route_service.set_route(
                normalized_category,
                normalized_step,
                interaction.channel.id,
            )

            await interaction.response.send_message(
                "✅ 현재 채널 등록 완료\n"
                f"- 카테고리: `{normalized_category}`\n"
                f"- 단계: `{normalized_step}`\n"
                f"- 채널: {interaction.channel.mention}\n"
                f"- 채널 ID: `{interaction.channel.id}`",
                ephemeral=True,
            )
        except Exception as exc:
            await interaction.response.send_message(
                f"❌ 현재 채널 설정 실패\n```{exc}```",
                ephemeral=True,
            )

    @app_commands.command(name="자동세팅", description="서버의 채널 이름을 자동 검색해서 라우팅을 등록합니다.")
    async def auto_setup_channels(self, interaction: discord.Interaction) -> None:
        if interaction.guild is None:
            await interaction.response.send_message("❌ 서버 안에서만 사용할 수 있습니다.", ephemeral=True)
            return

        if await _reject_if_not_manager(interaction):
            return

        mapping = {
            "건기식": {
                "input": "건기식-소싱-input",
                "text": "건기식-텍스트-pvw",
                "short": "건기식-숏폼-pvw",
                "publish": "건기식-송출-pgm",
            },
            "식품": {
                "input": "식품-소싱-input",
                "text": "식품-텍스트-pvw",
                "short": "식품-숏폼-pvw",
                "publish": "식품-송출-pgm",
            },
            "주방": {
                "input": "주방-소싱-input",
                "text": "주방-텍스트-pvw",
                "short": "주방-숏폼-pvw",
                "publish": "주방-송출-pgm",
            },
            "개발": {
                "input": "개발-소싱-input",
                "text": "개발-텍스트-pvw",
                "short": "개발-숏폼-pvw",
                "publish": "개발-송출-pgm",
            },
        }

        success: list[str] = []
        failed: list[str] = []

        for category, steps in mapping.items():
            for step, channel_name in steps.items():
                channel = discord.utils.get(interaction.guild.text_channels, name=channel_name)

                if channel is None:
                    failed.append(f"❌ {channel_name}")
                    continue

                try:
                    channel_route_service.set_route(category, step, channel.id)
                    success.append(f"✅ {category} / {step} → #{channel.name}")
                except Exception as exc:
                    failed.append(f"❌ {category} / {step} → {channel_name}: {exc}")

        message = ["🏢 자동 채널 세팅 완료\n"]

        if success:
            message.append("\n".join(success))

        if failed:
            message.append("\n\n찾지 못했거나 실패한 채널:\n" + "\n".join(failed))

        await _send_long_response(interaction, "".join(message), ephemeral=True)

    @app_commands.command(name="채널초기화", description="특정 카테고리의 채널 설정을 삭제합니다.")
    @app_commands.describe(category="초기화할 카테고리")
    @app_commands.choices(category=CATEGORY_CHOICES)
    async def clear_channel_routes(
        self,
        interaction: discord.Interaction,
        category: app_commands.Choice[str],
    ) -> None:
        if await _reject_if_not_manager(interaction):
            return

        try:
            normalized = channel_route_service.normalize_category(category.value)
            channel_route_service.clear_category(normalized)
            await interaction.response.send_message(
                f"🧹 `{normalized}` 카테고리의 채널 설정을 초기화했습니다.",
                ephemeral=True,
            )
        except Exception as exc:
            await interaction.response.send_message(
                f"❌ 초기화 실패\n```{exc}```",
                ephemeral=True,
            )


class SingleCommands(app_commands.Group):
    """싱글봇 테스트/운영용 슬래시 명령어 그룹."""

    def __init__(self) -> None:
        super().__init__(
            name="single",
            description="단일 디렉터 봇 테스트 명령어",
        )

    @app_commands.command(name="테스트기획", description="이미지 없이 전체 워크플로우를 테스트합니다.")
    @app_commands.describe(
        category="카테고리",
        platform="플랫폼",
        trigger_word="댓글 유도 단어",
        coupang_link="쿠팡 파트너스 링크",
        topic="기획 주제",
    )
    @app_commands.choices(category=CATEGORY_CHOICES, platform=PLATFORM_CHOICES)
    async def test_planning(
        self,
        interaction: discord.Interaction,
        category: app_commands.Choice[str],
        platform: app_commands.Choice[str],
        trigger_word: str,
        coupang_link: str,
        topic: str,
    ) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            memory = JobMemory(
                category=channel_route_service.normalize_category(category.value),
                platform=platform.value,
                trigger_word=trigger_word,
                coupang_link=coupang_link,
                topic=topic,
                image_available=False,
            )

            if interaction.channel:
                job_memory[interaction.channel.id] = memory

            await interaction.followup.send(
                "🧪 이미지 없는 테스트 기획을 시작합니다.\n"
                "저장된 채널 설정이 있으면 단계별 결과가 지정 채널로 이동합니다.",
                ephemeral=True,
            )

            await run_full_workflow(
                interaction.channel,
                memory,
                image=None,
                guild=interaction.guild,
            )

        except Exception as exc:
            await interaction.followup.send(
                f"❌ 테스트 기획 실패\n```{exc}```",
                ephemeral=True,
            )

    @app_commands.command(name="기획시작", description="텍스트 기반 기획을 시작합니다.")
    @app_commands.describe(
        category="카테고리",
        platform="플랫폼",
        trigger_word="댓글 유도 단어",
        coupang_link="쿠팡 파트너스 링크",
        topic="기획 주제",
    )
    @app_commands.choices(category=CATEGORY_CHOICES, platform=PLATFORM_CHOICES)
    async def start_planning(
        self,
        interaction: discord.Interaction,
        category: app_commands.Choice[str],
        platform: app_commands.Choice[str],
        trigger_word: str,
        coupang_link: str,
        topic: str,
    ) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            memory = JobMemory(
                category=channel_route_service.normalize_category(category.value),
                platform=platform.value,
                trigger_word=trigger_word,
                coupang_link=coupang_link,
                topic=topic,
                image_available=False,
            )

            if interaction.channel:
                job_memory[interaction.channel.id] = memory

            await interaction.followup.send(
                "📢 신규 오더 접수\n"
                f"- 카테고리: `{memory.category}`\n"
                f"- 플랫폼: `{platform.value}`\n"
                f"- 댓글 단어: `{trigger_word}`\n"
                f"- 주제: `{topic}`\n"
                "슬래시 버전은 현재 이미지 없이 진행합니다.",
                ephemeral=True,
            )

            await run_full_workflow(
                interaction.channel,
                memory,
                image=None,
                guild=interaction.guild,
            )

        except Exception as exc:
            await interaction.followup.send(
                f"❌ 기획 시작 실패\n```{exc}```",
                ephemeral=True,
            )


class MultiCommands(app_commands.Group):
    """멀티봇 운영용 슬래시 명령어 그룹."""

    def __init__(self) -> None:
        super().__init__(
            name="multi",
            description="11개 멀티봇 운영 명령어",
        )

    @app_commands.command(name="상태", description="멀티봇 모드 상태와 봇 ID 매핑을 확인합니다.")
    async def multi_status(self, interaction: discord.Interaction) -> None:
        lines = [
            "🤖 **멀티봇 상태**",
            f"- SINGLE_BOT_MODE: `{settings.single_bot_mode}`",
            "",
            "**등록된 봇 ID**",
        ]

        if not bot_ids:
            lines.append("- 아직 등록된 봇 ID가 없습니다.")
        else:
            for key, bot_id in bot_ids.items():
                lines.append(f"- `{key}` → `{bot_id}`")

        await _send_long_response(interaction, "\n".join(lines), ephemeral=True)

    @app_commands.command(name="안내", description="싱글봇/멀티봇 명령어 사용 방식을 안내합니다.")
    async def multi_help(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "🧭 **명령어 구분 안내**\n\n"
            "**관리 설정**\n"
            "- `/admin 상태`\n"
            "- `/admin gemini테스트`\n"
            "- `/admin 자동세팅`\n"
            "- `/admin 채널목록`\n\n"
            "**단일 봇 테스트**\n"
            "- `/single 테스트기획`\n"
            "- `/single 기획시작`\n\n"
            "**멀티봇 운영**\n"
            "- `/multi 상태`\n"
            "- `/multi 안내`\n\n"
            "현재 워크플로우 실행은 director 봇이 담당합니다.",
            ephemeral=True,
        )


def register_slash_commands(bot: commands.Bot) -> None:
    """슬래시 명령어 그룹을 등록합니다."""
    for group_name in ("admin", "single", "multi"):
        existing = bot.tree.get_command(group_name)
        if existing is not None:
            bot.tree.remove_command(group_name)

    bot.tree.add_command(AdminCommands())
    bot.tree.add_command(SingleCommands())
    bot.tree.add_command(MultiCommands())


def create_single_bot() -> commands.Bot:
    """로컬 테스트용 단일 봇."""
    bot = create_bot("director", command_prefix="!")
    register_slash_commands(bot)
    return bot


def create_multi_bots() -> dict[str, commands.Bot]:
    """11개 봇 객체를 생성합니다.

    Slash command는 director 봇에만 등록합니다.
    나머지 봇은 역할별 작업 실행자로 확장할 수 있습니다.
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

    register_slash_commands(bots["director"])
    return bots
