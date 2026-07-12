from pathlib import Path
from typing import Dict, Optional, Tuple

from pygame import Surface
from pygame.font import Font
from pygame.image import load
from pygame.transform import scale


class AssetManager:
    def __init__(self, images_dir: Path, fonts_dir: Path):
        self.images_dir = images_dir
        self.fonts_dir = fonts_dir

        self._images: Dict[Tuple[str, Optional[Tuple[int, int]], bool], Surface] = {}
        self._fonts: Dict[Tuple[str, int], Font] = {}

    def image(
        self,
        name: str,
        size: Optional[Tuple[int, int]] = None,
        alpha: bool = True,
    ) -> Surface:
        key = (name, size, alpha)
        cached = self._images.get(key)
        if cached is not None:
            return cached

        surface = load(self.images_dir / name)
        surface = surface.convert_alpha() if alpha else surface.convert()

        if size is not None:
            surface = scale(surface, size)

        self._images[key] = surface
        return surface

    def font(self, name: str, size: int) -> Font:
        key = (name, size)
        cached = self._fonts.get(key)
        if cached is not None:
            return cached

        loaded_font = Font(self.fonts_dir / name, size)
        self._fonts[key] = loaded_font
        return loaded_font