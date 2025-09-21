from pygame import Surface, surfarray
from datetime import datetime
from numpy import uint8


current_strength = 0.0

def apply_blue_filter(screen: Surface, target_strength: float, fade_speed: float = 0.05):
    global current_strength

    delta = target_strength - current_strength
    current_strength += delta * fade_speed

    factor = 1 - current_strength
    arr = surfarray.pixels3d(screen)
    arr[..., 2] = (arr[..., 2] * factor).astype(uint8)
    del arr

def get_strength_by_time(max_strength: float = 0.25, virtual_hour: float = None):
    now = datetime.now()
    hour = virtual_hour or (now.hour + now.minute / 60)
    if 8 <= hour < 18:
        return 0.0
    elif 18 <= hour < 22:
        return (hour - 18) / 4 * max_strength
    elif 22 <= hour or hour < 6:
        return max_strength
    elif 6 <= hour < 8:
        return (1 - (hour - 6) / 2) * max_strength