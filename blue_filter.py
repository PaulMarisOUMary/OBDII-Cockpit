from datetime import datetime
from math import isclose
from typing import Optional, Tuple

from pygame import Surface, surfarray
from numpy import multiply

class BlueFilter:
    def __init__(self, max_strength: float = 0.5, fade_speed: float = 0.05):
        self.max_strength = max_strength
        self.fade_speed = fade_speed

        self.current_strength = 0.0
        self._last_strength = -1.0
        self._channel_scales: Optional[Tuple[float, float, float]] = None

    def apply(self, screen: Surface, target_strength: Optional[float] = None, virtual_hour: Optional[float] = None) -> None:
        target_strength = self.strength_by_time(virtual_hour) if target_strength is None else target_strength

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
        arr = surfarray.pixels3d(screen)
        multiply(arr[..., 0], red_scale, out=arr[..., 0], casting="unsafe")
        multiply(arr[..., 1], green_scale, out=arr[..., 1], casting="unsafe")
        multiply(arr[..., 2], blue_scale, out=arr[..., 2], casting="unsafe")

        del arr

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