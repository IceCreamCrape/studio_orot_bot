"""Discord 메시지 포맷 유틸리티."""

from __future__ import annotations

import discord


def make_section_embed(title: str, description: str, color: int = 0xBFA58A) -> discord.Embed:
    """통일된 스타일의 Embed를 만듭니다."""
    embed = discord.Embed(title=title, description=description[:3900], color=color)
    embed.set_footer(text="STUDIO OROT")
    return embed


def truncate(text: str, limit: int = 1800) -> str:
    """Discord 메시지 제한에 맞춰 텍스트를 자릅니다."""
    if len(text) <= limit:
        return text
    return text[: limit - 20] + "\n... [생략]"
