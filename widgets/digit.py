from typing import Dict, Tuple

from pygame import Surface
from pygame.font import Font


class Digit:
    _digit_cache: Dict[Tuple[Font, Tuple[int, int, int]], Tuple[Surface, ...]] = {}

    def __init__(self,
        font: Font,
        position: Tuple[int, int],
        n_digits: int = 3,
        color: Tuple[int, int, int] = (255, 255, 255),
        spacing: int = 0,
    ):
        self.font = font
        self.position = position
        self.n_digits = n_digits
        self.color = color
        self.spacing = spacing

        self._ordzero = ord('0')

        key = (self.font, self.color)
        if key not in self._digit_cache:
            self._digit_cache[key] = tuple(self.font.render(str(i), True, self.color) for i in range(10))

        self._cache = self._digit_cache[key]
        self._max_width = max(surf.get_width() for surf in self._cache)

    def draw(self, screen: Surface, value: int) -> None:
        text = f"{value:0{self.n_digits}d}"
        pos_x = self.position[0]
        pos_y = self.position[1]
        width_step = self._max_width + self.spacing
        
        for i in range(len(text)):
            surf = self._cache[ord(text[i]) - self._ordzero]
            x = pos_x + i * width_step + (self._max_width - surf.get_width())
            screen.blit(surf, (x, pos_y))