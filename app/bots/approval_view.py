"""최종 승인 버튼 UI.

Make.com 전송은 기본적으로 테스트 모드입니다.
ENABLE_MAKE_WEBHOOK=false이면 실제 전송하지 않고 Discord에 payload preview를 보여줍니다.
"""

from __future__ import annotations

import json

import discord

from app.services.webhook_service import webhook_service
from app.utils.discord_format import truncate


class ApprovalView(discord.ui.View):
    """최종 콘텐츠 승인 버튼."""

    def __init__(
        self,
        final_content: str,
        trigger_word: str,
        coupang_link: str,
        platform: str,
        timeout: float | None = 600,
    ) -> None:
        super().__init__(timeout=timeout)
        self.final_content = final_content
        self.trigger_word = trigger_word
        self.coupang_link = coupang_link
        self.platform = platform

    @discord.ui.button(
        label="발행 테스트 / Make.com 전송",
        style=discord.ButtonStyle.success,
        emoji="🚀",
    )
    async def approve_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        """승인 버튼 클릭 시 실행됩니다."""
        await interaction.response.defer(ephemeral=True)

        dm_text = (
            "안녕하세요! 오롯이 선별한 제품 정보입니다 🤍\n\n"
            f"👉 확인하기: {self.coupang_link}\n\n"
            "* 이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."
        )

        payload = {
            "source": "studio_orot_discord",
            "platform": self.platform,
            "post_content": self.final_content,
            "dm_trigger_word": self.trigger_word,
            "dm_message": dm_text,
            "raw_link": self.coupang_link,
        }

        result = await webhook_service.send_to_make(payload)

        preview = json.dumps(result.payload, ensure_ascii=False, indent=2)
        message = (
            f"{'✅' if result.ok else '❌'} {result.message}\n\n"
            f"```json\n{truncate(preview, 1600)}\n```"
        )

        await interaction.followup.send(message, ephemeral=True)

        if result.ok:
            button.disabled = True
            await interaction.message.edit(view=self)
