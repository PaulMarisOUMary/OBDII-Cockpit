from typing import Callable, List, Optional, Tuple

from pygame import Surface


class Gauge:
    def __init__(self, 
        image: Surface, 
        position: Tuple[int, int],
        max_value: int,
        ratio_fn: Optional[Callable[[int], float]] = None,
    ):
        self.image = image
        self.position = position

        self.max_value = max_value
        self.height = self.image.get_height()
        self.width = self.image.get_width()

        self.ratio_fn = ratio_fn or (lambda value: max(0.0, min(1.0, value / self.max_value)))

        self._prev_value = None
        self._prev_surface = None

    def draw(self, screen: Surface, value: int = 0) -> None:
        value = max(0, min(value, self.max_value))

        if self._prev_value == value and self._prev_surface is not None:
            screen.blit(self._prev_surface, (self.position[0], self.position[1] + self.height - self._prev_surface.get_height()))
            return

        ratio = self.ratio_fn(value)
        ratio = max(0.0, min(1.0, ratio))

        fill_height = int(ratio * self.height)

        if fill_height > 0:
            cropped = self.image.subsurface(
                (0, self.height - fill_height, self.width, fill_height)
            )
            self._prev_surface = cropped.copy()
            self._prev_value = value
            screen.blit(cropped, (self.position[0], self.position[1] + self.height - fill_height))
    
    @staticmethod
    def gauge_ratio(
        segments: List[Tuple[float, float]], 
        segment_pixels: List[int],
        scale: float = 1.0,
        value: float = 0,
    ) -> float:
        value *= scale
        total_pixels = sum(segment_pixels)
        filled_pixels = 0.0

        for (low, high), height in zip(segments, segment_pixels):
            if low <= value <= high:
                fraction = (value - low) / (high - low) if high - low > 0 else 0
                filled_pixels += fraction * height
                break
            else:
                filled_pixels += height

        ratio = filled_pixels / total_pixels
        return min(1.0, max(0.0, ratio))
