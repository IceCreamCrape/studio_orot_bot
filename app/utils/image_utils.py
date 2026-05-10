"""이미지 유틸리티."""

from __future__ import annotations

import io
from typing import Optional

import discord
from PIL import Image


async def read_first_image(message: discord.Message) -> Optional[Image.Image]:
    """메시지의 첫 번째 이미지 첨부파일을 PIL Image로 읽습니다.

    이미지가 없거나 열 수 없으면 None을 반환합니다.
    """
    if not message.attachments:
        return None

    attachment = message.attachments[0]
    content_type = attachment.content_type or ""

    if not content_type.startswith("image/"):
        return None

    raw = await attachment.read()
    image = Image.open(io.BytesIO(raw))
    return image.convert("RGB")
