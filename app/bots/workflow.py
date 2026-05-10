"""콘텐츠 제작 워크플로우.

SINGLE_BOT_MODE에서는 한 개 봇이 이 클래스를 호출해 전체 프로세스를 순서대로 수행합니다.
MULTI_BOT_MODE에서는 각 역할 봇의 메시지 이벤트에서 이 로직을 나누어 호출할 수 있도록
함수를 잘게 분리해두었습니다.
"""

from __future__ import annotations

import discord

from app.bots.approval_view import ApprovalView
from app.bots.registry import JobMemory
from app.services.gemini_service import gemini_service
from app.utils.discord_format import make_section_embed


def select_analyst(category: str) -> str:
    """카테고리에 맞는 애널리스트 페르소나를 선택합니다."""
    if category == "건기식":
        return "analyst_health"
    if category == "식품":
        return "analyst_food"
    return "analyst_living"


def select_creative(platform: str) -> str:
    """플랫폼에 맞는 크리에이티브 페르소나를 선택합니다."""
    if platform == "쓰레드":
        return "creative_threads"
    if platform == "블로그":
        return "creative_blog"
    if platform == "틱톡":
        return "marketer_tiktok"
    return "creative_instagram"


async def run_full_workflow(
    channel: discord.abc.Messageable,
    memory: JobMemory,
    image=None,
) -> str:
    """단일 봇 모드에서 전체 워크플로우를 한 번에 실행합니다.

    Discord 안에서 테스트하기 쉽게 모든 단계를 순서대로 출력합니다.
    """

    # 1. 상품/카테고리 분석
    analyst_key = select_analyst(memory.category)
    analysis_prompt = (
        f"다음 상품을 분석하세요.\n"
        f"카테고리: {memory.category}\n"
        f"플랫폼: {memory.platform}\n"
        f"주제: {memory.topic}\n"
        "소싱 포인트 3가지와 주의해야 할 표현을 정리하세요."
    )
    analysis = await gemini_service.generate(analyst_key, analysis_prompt, image=image)
    memory.add_step("상품 분석", analysis)
    await channel.send(embed=make_section_embed("📊 1단계: 상품 분석", analysis))

    # 2. 타겟 전략
    strategy_prompt = (
        f"{memory.as_context()}\n\n"
        "위 분석을 바탕으로 타겟 고객의 Pain Point와 구매 설득 방향을 작성하세요."
    )
    strategy = await gemini_service.generate("marketer_strategy", strategy_prompt)
    memory.add_step("타겟 전략", strategy)
    await channel.send(embed=make_section_embed("🎯 2단계: 타겟 전략", strategy))

    # 3. 플랫폼별 콘텐츠 생성
    creative_key = select_creative(memory.platform)
    creative_prompt = (
        f"{memory.as_context()}\n\n"
        f"{memory.platform}용 콘텐츠 초안을 작성하세요. "
        "본문에 직접 구매 링크는 넣지 말고 댓글 유도형 CTA를 사용하세요."
    )
    creative = await gemini_service.generate(creative_key, creative_prompt)
    memory.add_step("콘텐츠 초안", creative)
    await channel.send(embed=make_section_embed("✍️ 3단계: 콘텐츠 초안", creative))

    # 4. 블로그일 경우 썸네일 프롬프트도 생성
    if memory.platform == "블로그":
        visual_prompt = (
            f"{memory.as_context()}\n\n"
            "블로그 썸네일용 AI 이미지 생성 프롬프트를 영어로 작성하세요."
        )
        visual = await gemini_service.generate("creative_visual", visual_prompt)
        memory.add_step("비주얼 프롬프트", visual)
        await channel.send(embed=make_section_embed("🖼️ 4단계: 비주얼 프롬프트", visual))

    # 5. 해시태그
    tag_prompt = (
        f"{memory.as_context()}\n\n"
        f"{memory.platform}에 맞는 해시태그 세트를 제안하세요."
    )
    tags = await gemini_service.generate("marketer_tag", tag_prompt)
    memory.add_step("해시태그", tags)
    await channel.send(embed=make_section_embed("🏷️ 5단계: 해시태그", tags))

    # 6. 최종 검수
    director_prompt = (
        f"{memory.as_context()}\n\n"
        "최종 게시물로 다듬으세요. "
        f"하단에 반드시 '댓글로 [{memory.trigger_word}]를 남겨주시면 DM으로 정보를 보내드릴게요 🤍' "
        "문구를 자연스럽게 포함하세요. 과대광고 표현은 제거하세요."
    )
    final_content = await gemini_service.generate("director", director_prompt)
    memory.add_step("최종 검수", final_content)

    view = ApprovalView(
        final_content=final_content,
        trigger_word=memory.trigger_word,
        coupang_link=memory.coupang_link,
        platform=memory.platform,
    )
    await channel.send(
        embed=make_section_embed("👑 최종 검수 및 발행 대기", final_content),
        view=view,
    )

    return final_content
