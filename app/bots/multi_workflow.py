"""11개 봇이 실제로 각자 말하는 멀티봇 워크플로우.

대화/보고 메시지는 공통 #봇회의실로,
오류/시스템 로그는 공통 #시스템-로그로 보냅니다.
"""

from __future__ import annotations

import traceback
from collections.abc import Mapping

import discord
from discord.ext import commands

from app.services.gemini_image_service import gemini_image_service
import discord

from app.bots.approval_view import ApprovalView
from app.bots.registry import JobMemory
from app.services.channel_route_service import channel_route_service
from app.services.gemini_service import gemini_service
from app.utils.discord_format import make_section_embed


BotMap = Mapping[str, commands.Bot]


def select_analyst(category: str) -> str:
    if category == "건기식":
        return "analyst_health"
    if category == "식품":
        return "analyst_food"
    return "analyst_living"


def select_creative(platform: str) -> str:
    if platform == "쓰레드":
        return "creative_threads"
    if platform == "블로그":
        return "creative_blog"
    if platform in {"틱톡", "숏폼", "릴스"}:
        return "marketer_tiktok"
    return "creative_instagram"


def display_role(role_key: str) -> str:
    names = {
        "director": "👑 총괄 디렉터",
        "analyst_health": "💊 건기식 애널리스트",
        "analyst_food": "🍔 식품 애널리스트",
        "analyst_living": "🍳 리빙/주방 애널리스트",
        "marketer_strategy": "📈 타겟 전략가",
        "creative_instagram": "🎨 인스타그램 에디터",
        "creative_threads": "🧵 쓰레드 에디터",
        "creative_blog": "📝 블로그 에디터",
        "creative_visual": "🖼️ 비주얼 프롬프터",
        "marketer_tiktok": "⚡ 틱톡 바이럴 전략가",
        "marketer_tag": "🏷️ 해시태그 전문가",
    }
    return names.get(role_key, role_key)


async def _resolve_output_channel(
    guild: discord.Guild | None,
    fallback_channel: discord.abc.Messageable,
    category: str,
    step: str,
) -> discord.abc.Messageable:
    return await channel_route_service.resolve_channel(
        guild=guild,
        fallback_channel=fallback_channel,
        category=category,
        step=step,
    )


async def _common_channel(
    guild: discord.Guild | None,
    fallback_channel: discord.abc.Messageable,
    step: str,
) -> discord.abc.Messageable:
    return await channel_route_service.resolve_common_channel(
        guild=guild,
        fallback_channel=fallback_channel,
        step=step,
    )


async def _send_as(
    bot: commands.Bot,
    target_channel: discord.abc.Messageable,
    *,
    title: str,
    content: str,
    color: int = 0xBFA58A,
    view: discord.ui.View | None = None,
) -> discord.Message | None:
    embed = make_section_embed(title, content, color=color)

    channel_to_send = target_channel
    channel_id = getattr(target_channel, "id", None)

    if channel_id is not None:
        cached = bot.get_channel(channel_id)
        if cached is not None:
            channel_to_send = cached
        else:
            try:
                channel_to_send = await bot.fetch_channel(channel_id)
            except Exception as exc:
                print(f"❌ 채널 fetch 실패: {channel_id} / {exc}", flush=True)
                return None

    try:
        return await channel_to_send.send(embed=embed, view=view)
    except Exception as exc:
        print(f"❌ 메시지 전송 실패: bot={bot.user} channel={channel_id} error={exc}", flush=True)
        return None


async def _log_system(
    bots: BotMap,
    origin_channel: discord.abc.Messageable,
    guild: discord.Guild | None,
    *,
    title: str,
    content: str,
) -> None:
    """시스템 로그를 공통 log 채널로 보냅니다."""
    log_channel = await _common_channel(guild, origin_channel, "log")
    director_bot = bots.get("director")
    if director_bot is None:
        print(f"[SYSTEM LOG] {title}: {content}", flush=True)
        return

    await _send_as(
        director_bot,
        log_channel,
        title=f"🚨 {title}",
        content=content,
        color=0xFF5555,
    )


async def _meeting_report(
    bots: BotMap,
    origin_channel: discord.abc.Messageable,
    guild: discord.Guild | None,
    *,
    sender_key: str,
    title: str,
    content: str,
) -> None:
    """봇회의실에 업무 보고 메시지를 보냅니다."""
    meeting_channel = await _common_channel(guild, origin_channel, "meeting")
    sender_bot = bots[sender_key]

    await _send_as(
        sender_bot,
        meeting_channel,
        title=title,
        content=content,
    )


async def run_multi_bot_workflow(
    bots: BotMap,
    origin_channel: discord.abc.Messageable,
    memory: JobMemory,
    *,
    image=None,
    guild: discord.Guild | None = None,
) -> str:
    """11개 봇이 실제 대화처럼 단계별 메시지를 보내는 워크플로우."""

    try:
        director_bot = bots["director"]
        analyst_key = select_analyst(memory.category)
        analyst_bot = bots[analyst_key]
        strategy_bot = bots["marketer_strategy"]
        creative_key = select_creative(memory.platform)
        creative_bot = bots[creative_key]
        tag_bot = bots["marketer_tag"]

        input_channel = await _resolve_output_channel(guild, origin_channel, memory.category, "input")
        text_channel = await _resolve_output_channel(guild, origin_channel, memory.category, "text")
        short_channel = await _resolve_output_channel(guild, origin_channel, memory.category, "short")
        publish_channel = await _resolve_output_channel(guild, origin_channel, memory.category, "publish")

        await _meeting_report(
            bots,
            origin_channel,
            guild,
            sender_key="director",
            title="📢 신규 오더 접수",
            content=(
                f"{display_role(analyst_key)} 님, 상품 분석을 시작해주세요.\n\n"
                f"- 카테고리: `{memory.category}`\n"
                f"- 플랫폼: `{memory.platform}`\n"
                f"- 댓글 단어: `{memory.trigger_word}`\n"
                f"- 주제: {memory.topic}"
            ),
        )

        analysis_prompt = (
            f"다음 상품을 분석하세요.\n"
            f"카테고리: {memory.category}\n"
            f"플랫폼: {memory.platform}\n"
            f"주제: {memory.topic}\n"
            "소싱 포인트 3가지와 주의해야 할 표현을 정리하세요."
        )
        analysis = await gemini_service.generate(analyst_key, analysis_prompt, image=image)
        memory.add_step(display_role(analyst_key), analysis)

        await _send_as(
            analyst_bot,
            input_channel,
            title=f"📊 1단계: {display_role(analyst_key)} 상품 분석",
            content=analysis,
        )

        await _meeting_report(
            bots,
            origin_channel,
            guild,
            sender_key=analyst_key,
            title="📨 분석 완료 보고",
            content=f"{display_role('marketer_strategy')} 님, 타겟 전략으로 넘깁니다.",
        )

        strategy_prompt = (
            f"{memory.as_context()}\n\n"
            "위 분석을 바탕으로 타겟 고객의 Pain Point와 구매 설득 방향을 작성하세요."
        )
        strategy = await gemini_service.generate("marketer_strategy", strategy_prompt)
        memory.add_step(display_role("marketer_strategy"), strategy)

        await _send_as(
            strategy_bot,
            text_channel,
            title="🎯 2단계: 타겟 전략",
            content=strategy,
        )

        await _meeting_report(
            bots,
            origin_channel,
            guild,
            sender_key="marketer_strategy",
            title="📨 전략 완료 보고",
            content=f"{display_role(creative_key)} 님, 플랫폼 콘텐츠 초안을 작성해주세요.",
        )

        creative_prompt = (
            f"{memory.as_context()}\n\n"
            f"{memory.platform}용 콘텐츠 초안을 작성하세요. "
            "본문에 직접 구매 링크는 넣지 말고 댓글 유도형 CTA를 사용하세요."
        )
        creative = await gemini_service.generate(creative_key, creative_prompt)
        memory.add_step(display_role(creative_key), creative)

        creative_channel = short_channel if memory.platform in {"틱톡", "릴스", "숏폼"} else text_channel

        await _send_as(
            creative_bot,
            creative_channel,
            title=f"✍️ 3단계: {display_role(creative_key)} 콘텐츠 초안",
            content=creative,
        )

        if memory.platform == "블로그":
            visual_bot = bots["creative_visual"]

            await _meeting_report(
                bots,
                origin_channel,
                guild,
                sender_key=creative_key,
                title="📨 블로그 초안 완료 보고",
                content=f"{display_role('creative_visual')} 님, 썸네일 프롬프트를 작성해주세요.",
            )

            visual_prompt = (
                f"{memory.as_context()}\n\n"
                "블로그 썸네일용 AI 이미지 생성 프롬프트를 영어로 작성하세요."
            )
            visual = await gemini_service.generate("creative_visual", visual_prompt)
            image_path = gemini_image_service.generate_image(
                        prompt=visual,
                        filename="blog_visual.png",
            )
            memory.add_step(display_role("creative_visual"), visual)

            await _send_as(
                visual_bot,
                text_channel,
                title="🖼️ 4단계: 비주얼 프롬프트",
                content=visual,
            )

            if image_path:
                target_channel = visual_bot.get_channel(text_channel.id)

                if target_channel:
                    await target_channel.send(
                        content="🎨 Gemini 생성 이미지",
                        file=discord.File(str(image_path)),
                    )

        await _meeting_report(
            bots,
            origin_channel,
            guild,
            sender_key=creative_key,
            title="📨 콘텐츠 완료 보고",
            content=f"{display_role('marketer_tag')} 님, 해시태그 세트를 추출해주세요.",
        )

        tag_prompt = (
            f"{memory.as_context()}\n\n"
            f"{memory.platform}에 맞는 해시태그 세트를 제안하세요."
        )
        tags = await gemini_service.generate("marketer_tag", tag_prompt)
        memory.add_step(display_role("marketer_tag"), tags)

        await _send_as(
            tag_bot,
            text_channel,
            title="🏷️ 5단계: 해시태그 세트",
            content=tags,
        )

        await _meeting_report(
            bots,
            origin_channel,
            guild,
            sender_key="marketer_tag",
            title="📨 태그 완료 보고",
            content=f"{display_role('director')} 님, 최종 검수 부탁드립니다.",
        )

        director_prompt = (
            f"{memory.as_context()}\n\n"
            "최종 게시물로 다듬으세요. "
            f"하단에 반드시 '댓글로 [{memory.trigger_word}]를 남겨주시면 DM으로 정보를 보내드릴게요 🤍' "
            "문구를 자연스럽게 포함하세요. 과대광고 표현은 제거하세요."
        )
        final_content = await gemini_service.generate("director", director_prompt)
        memory.add_step(display_role("director"), final_content)

        view = ApprovalView(
            final_content=final_content,
            trigger_word=memory.trigger_word,
            coupang_link=memory.coupang_link,
            platform=memory.platform,
        )

        await _send_as(
            director_bot,
            publish_channel,
            title="👑 최종 검수 및 발행 대기",
            content=final_content,
            view=view,
        )

        await _meeting_report(
            bots,
            origin_channel,
            guild,
            sender_key="director",
            title="✅ 프로젝트 완료",
            content=(
                f"`{memory.topic}` 기획안이 완료되었습니다.\n"
                f"최종 검수본은 송출 채널에서 확인해주세요."
            ),
        )

        return final_content

    except Exception as exc:
        await _log_system(
            bots,
            origin_channel,
            guild,
            title="멀티봇 워크플로우 오류",
            content=f"```{traceback.format_exc()[-1800:]}```",
        )
        raise exc
