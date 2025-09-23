from typing import Any, Tuple

from pygame import Color, Surface
from pygame.font import Font
from pygame.image import load
from pygame.transform import scale

def render_text(font: Font, text: str, color: Color) -> Surface:
    return font.render(text, True, color)

def load_scale_image(image_path: str, size: Tuple[int, int]) -> Surface:
    return scale(load(image_path), size)

def safe_int(value: Any) -> int:
    if not isinstance(value, (int, float)):
        return 0
    return int(value)