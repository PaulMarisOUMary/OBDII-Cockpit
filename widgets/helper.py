from pathlib import Path
from typing import Any, Tuple

from pygame import Surface
from pygame.font import Font
from pygame.image import load
from pygame.transform import scale

def render_text(font: Font, text: str, color: Tuple[int, int, int]) -> Surface:
    return font.render(text, True, color).convert_alpha()

def load_scale_image(image_path: Path, size: Tuple[int, int]) -> Surface:
    return scale(load(image_path).convert_alpha(), size)

def safe_int(value: Any) -> int:
    if not isinstance(value, (int, float)):
        return 0
    return int(value)