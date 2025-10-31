from typing import Optional
from pygame import Surface, surfarray
from datetime import datetime
from numpy import uint8, clip

class BlueFilter:
    def __init__(self, max_strength: float = 0.5, fade_speed: float = 0.05):
        self.max_strength = max_strength
        self.fade_speed = fade_speed

        self.current_strength = 0.0
        self._last_strength = -1.0

    def apply(self, screen: Surface, target_strength: Optional[float] = None, virtual_hour: Optional[float] = None) -> None:
        target_strength = target_strength or self.strength_by_time(virtual_hour)

        delta = target_strength - self.current_strength
        self.current_strength += delta * self.fade_speed

        self.current_strength = max(0.0, min(self.current_strength, self.max_strength))

        if abs(self.current_strength - self._last_strength) < 0.001:
            return
            
        self._last_strength = self.current_strength

        blue_factor = 1 - self.current_strength
        green_factor = 1 - self.current_strength * 0.5
        red_factor = 1

        arr = surfarray.pixels3d(screen)
        arr[..., 0] = clip(arr[..., 0] * red_factor, 0, 255).astype(uint8)
        arr[..., 1] = clip(arr[..., 1] * green_factor, 0, 255).astype(uint8)
        arr[..., 2] = clip(arr[..., 2] * blue_factor, 0, 255).astype(uint8)
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