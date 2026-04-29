from pathlib import Path

from nonebot.adapters.onebot.v11 import Message, MessageSegment


def send_image(img_path: str | Path | None = None, img_bytes: bytes | None = None) -> Message:
    if img_bytes:
        return Message(MessageSegment.image(img_bytes))
    if img_path:
        return Message(MessageSegment.image(Path(img_path).read_bytes()))
    return Message(MessageSegment.text(""))
