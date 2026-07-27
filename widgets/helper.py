from typing import Any, Tuple

from pygame import Surface
from pygame.font import Font


def render_text(font: Font, text: str, color: Tuple[int, int, int]) -> Surface:
    return font.render(text, True, color).convert_alpha()

def safe_int(value: Any) -> int:
    if not isinstance(value, (int, float)):
        return 0
    return int(value)