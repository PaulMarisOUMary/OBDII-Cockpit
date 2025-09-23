from typing import Dict, Tuple

from pygame import Color, Surface
from pygame.font import Font


class Digit:
    _digit_cache: Dict[Tuple[Font, Color], Tuple[Surface]] = {}

    def __init__(self,
        font: Font,
        position: Tuple[int, int],
        n_digits: int = 3,
        color: Color = Color(255, 255, 255),
        spacing: int = 0,
    ):
        self.font = font
        self.position = position
        self.n_digits = n_digits
        self.color = color
        self.spacing = spacing

        key = (self.font, self.color)
        if key not in self._digit_cache:
            self._digit_cache[key] = tuple(self.font.render(str(i), True, self.color) for i in range(10))

        self._cache = self._digit_cache[key]
        self._max_width = max(surf.get_width() for surf in self._cache)

    def draw(self, screen: Surface, value: int) -> None:
        text = f"{value:0{self.n_digits}d}"
        for i, digit in enumerate(text):
            surf = self._cache[int(digit)]
            x = self.position[0] + i * (self._max_width + self.spacing) + (self._max_width - surf.get_width())
            screen.blit(surf, (x, self.position[1]))