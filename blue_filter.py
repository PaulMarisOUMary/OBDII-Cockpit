from datetime import datetime
from math import isclose
from typing import Optional, Tuple

from pygame import Surface, BLEND_MULT


class BlueFilter:
    def __init__(self, max_strength: float = 0.5, fade_speed: float = 0.05):
        self.max_strength = max_strength
        self.fade_speed = fade_speed

        self.current_strength = 0.0
        self._last_strength = -1.0
        self._channel_scales: Optional[Tuple[float, float, float]] = None

        self._overlay: Optional[Surface] = None

    def apply(self, screen: Surface, target_strength: Optional[float] = None, virtual_hour: Optional[float] = None) -> None:
        target_strength = target_strength or self.strength_by_time(virtual_hour)

        self.current_strength += (target_strength - self.current_strength) * self.fade_speed
        self.current_strength = max(0.0, min(self.current_strength, self.max_strength))

        if not isclose(self.current_strength, self._last_strength, abs_tol=0.001):
            self._last_strength = self.current_strength
            if self.current_strength <= 0.001:
                self._channel_scales = None
            else:
                self._channel_scales = (
                    1.0,
                    1.0 - self.current_strength * 0.5,
                    1.0 - self.current_strength,
                )

        factors = self._channel_scales
        if factors is None:
            return

        red_scale, green_scale, blue_scale = factors

        if self._overlay is None or self._overlay.get_size() != screen.get_size():
            self._overlay = Surface(screen.get_size()).convert()

        self._overlay.fill((
            int(255 * red_scale),
            int(255 * green_scale),
            int(255 * blue_scale),
        ))
        screen.blit(self._overlay, (0, 0), special_flags=BLEND_MULT)

    def strength_by_time(self, virtual_hour: Optional[float] = None) -> float:
        now = datetime.now()
        hour = virtual_hour or (now.hour + now.minute / 60)

        if 8 <= hour < 18:
            return 0.0
        elif 18 <= hour < 22:
            return (hour - 18) / 4 * self.max_strength
        elif 22 <= hour or hour < 6:
            return self.max_strength
        elif 6 <= hour < 8:
            return (1 - (hour - 6) / 2) * self.max_strength
        return 0.0