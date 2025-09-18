from threading import Lock
from typing import Any, Dict
import pygame


IMG_PATHS = {
    "dashboard": "./assets/img/dashboard.png",
    "left_bar": "./assets/img/left_bar.png",
    "left_group_bar": "./assets/img/left_group_bar.png",
}

FONT_PATHS = {
    "big": "./fonts/Sarpanch-SemiBold.ttf",
    "small": "./fonts/Sarpanch-Regular.ttf",
}

SIZES = {
    "dashboard": (1280, 400),
    "left_bar": (130, 325),
    "left_group": (91, 118),
}


DIGIT_WIDTH = 50
SPEED_POS = (258, 60)
KMH_POS = (SPEED_POS[0] + DIGIT_WIDTH, SPEED_POS[1] + 95)
RPM_POS = (808, 53)
RPM_TEXT_POS = (RPM_POS[0] + int(DIGIT_WIDTH*1.5), RPM_POS[1] + 95)
LEFT_BAR_POS = (103, 38)
RIGHT_BAR_POS = (1047, 38)
LEFT_GROUP_BAR_POS = (210, 245)
LEFT_GROUP_BAR_POS_BIS = (295, 245)
RIGHT_GROUP_BAR_POS = (974, 245)

MAX_SPEED = 170
MAX_RPM = 6375
MAX_LOAD = 100
MAX_COOLANT = 150
MAX_OIL = 300



def load_and_scale_image(image_path: str, size: tuple[int, int]) -> pygame.Surface:
    """Load and scale an image to a specific size."""
    return pygame.transform.scale(pygame.image.load(image_path), size)

def render_text(text: str, font: pygame.font.Font, color: tuple[int, int, int]) -> pygame.Surface:
    """Render text using a specified font and color."""
    return font.render(text, True, color)

def get_centered_rect(image: pygame.Surface, screen_width: int, screen_height: int) -> pygame.Rect:
    """Return a centered rectangle for an image."""
    rect = image.get_rect()
    rect.center = (screen_width // 2, screen_height // 2 + 5)
    return rect

def draw_vertical_bar(
    screen: pygame.Surface,
    bar_img: pygame.Surface,
    value: int,
    max_value: int,
    position: tuple[int, int],
    piecewise: bool = False
) -> None:
    height = bar_img.get_height()
    value = max(0, min(value, max_value))

    if piecewise:
        low_range = 2000
        high_range = 6000
        low_offset = 0.0
        high_offset = 0.060

        mid_ratio = 0.475 - low_offset
        top_ratio = 1.0 - mid_ratio - high_offset

        if value <= low_range:
            ratio = (value / low_range) * mid_ratio
        elif value <= high_range:
            upper_ratio = (value - low_range) / (high_range - low_range)
            ratio = mid_ratio + upper_ratio * top_ratio
        else:
            ratio = mid_ratio + top_ratio
    else:
        ratio = value / max_value

    ratio = min(1.0, max(0.0, ratio))
    fill_height = int(ratio * height)

    if fill_height > 0:
        cropped = bar_img.subsurface((0, height - fill_height, bar_img.get_width(), fill_height))
        screen.blit(cropped, (position[0], position[1] + height - fill_height))


def draw_speed_text(screen: pygame.Surface, speed: int, font: pygame.font.Font, position: tuple, n: int = 3) -> None:
    """Render the 3-digit speed."""
    text = f"{speed:0{n}d}"
    for i, digit in enumerate(text):
        rendered = render_text(digit, font, (255, 255, 255))
        x = position[0] + (i + 1) * DIGIT_WIDTH - rendered.get_width()
        screen.blit(rendered, (x, position[1]))


dashboard = load_and_scale_image(IMG_PATHS["dashboard"], SIZES["dashboard"])
left_bar = load_and_scale_image(IMG_PATHS["left_bar"], SIZES["left_bar"])
right_bar = pygame.transform.flip(left_bar.copy(), True, False)
left_group_bar = load_and_scale_image(IMG_PATHS["left_group_bar"], SIZES["left_group"])
right_group_bar = pygame.transform.flip(left_group_bar.copy(), True, False)

big_font = pygame.font.Font(FONT_PATHS["big"], 80)
small_font = pygame.font.Font(FONT_PATHS["small"], 20)

label_kmh = render_text("km/h", small_font, (255, 255, 255))
label_rpm = render_text("RPM", small_font, (255, 255, 255))

def safe_int(value) -> int:
    if not isinstance(value, (int, float)):
        return 0
    return int(value)

def draw_dashboard(screen: pygame.Surface, storage: Dict[str, Any]) -> None:
    """Render the dashboard visuals."""

    speed = safe_int(storage.get("VEHICLE_SPEED", 0))
    load = safe_int(storage.get("ENGINE_LOAD", 0))
    rpm = safe_int(storage.get("ENGINE_SPEED", 0))
    # in_press = checker(storage.get("INTAKE_PRESSURE", 0))
    # baro = checker(storage.get("BAROMETRIC_PRESSURE", 0))
    coolant = safe_int(storage.get("ENGINE_COOLANT_TEMP", 0))
    # oil = checker(storage.get("ENGINE_OIL_TEMP", 0))

    # boost_kpa = in_press - (baro or 1000)

    # if rpm > 1500 and boost_kpa > 15:
    #     print("TURRBOOOOO")

    screen.blit(dashboard, (0, 0))

    draw_vertical_bar(screen, left_bar, speed, MAX_SPEED, LEFT_BAR_POS)
    draw_vertical_bar(screen, right_bar, rpm, MAX_RPM, RIGHT_BAR_POS, piecewise=True)
    # draw_vertical_bar(screen, left_group_bar, oil, MAX_OIL, LEFT_GROUP_BAR_POS)
    draw_vertical_bar(screen, left_group_bar, coolant, MAX_COOLANT, LEFT_GROUP_BAR_POS_BIS)
    draw_vertical_bar(screen, right_group_bar, load, MAX_LOAD, RIGHT_GROUP_BAR_POS)

    draw_speed_text(screen, speed, big_font, SPEED_POS)
    screen.blit(label_kmh, KMH_POS)

    draw_speed_text(screen, rpm, big_font, RPM_POS, 4)
    screen.blit(label_rpm, RPM_TEXT_POS)

    pygame.display.flip()
