from threading import Lock
from typing import Any, Dict
import pygame


IMG_PATHS = {
    "bg": "./assets/img/bg.png",
    "c3": "./assets/img/c3.png",
    "logo": "./assets/img/logo.png",
    "new_logo": "./assets/img/new_logo.png",
    "coolant": "./assets/img/coolant.png",
    "oil": "./assets/img/oil.png",
    "engine": "./assets/img/engine.png",
    "left": "./assets/img/left.png",
    "left_bar": "./assets/img/left_bar.png",
    "left_group": "./assets/img/left_group.png",
    "left_group_bar": "./assets/img/left_group_bar.png",
    "red_bar": "./assets/img/redbar.png",
    "orange_bar": "./assets/img/orangebar.png",
}

FONT_PATHS = {
    "big": "./fonts/Sarpanch-SemiBold.ttf",
    "small": "./fonts/Sarpanch-Regular.ttf",
}

SIZES = {
    "left": (618, 400),
    "left_bar": (130, 325),
    "left_group": (91, 118),
    "bg": (947, 343),
    "logo": (64, 59),
    "new_logo": (204, 204),
    "red_bar": (24, 31),
    "orange_bar": (24, 31),
    "c3": (500, 281),
    "oil": (25, 25),
    "coolant": (25, 25),
    "engine": (16, 16),
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


v = 0
rp = 0
l = 0
c = 0
o = 0



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


left = load_and_scale_image(IMG_PATHS["left"], SIZES["left"])
right = pygame.transform.flip(left.copy(), True, False)
left_bar = load_and_scale_image(IMG_PATHS["left_bar"], SIZES["left_bar"])
right_bar = pygame.transform.flip(left_bar.copy(), True, False)
left_group = load_and_scale_image(IMG_PATHS["left_group"], SIZES["left_group"])
left_group_bis = load_and_scale_image(IMG_PATHS["left_group"], SIZES["left_group"])
left_group_bar = load_and_scale_image(IMG_PATHS["left_group_bar"], SIZES["left_group"])
right_group = pygame.transform.flip(left_group.copy(), True, False)
right_group_bar = pygame.transform.flip(left_group_bar.copy(), True, False)
bg = load_and_scale_image(IMG_PATHS["bg"], SIZES["bg"])
c3 = load_and_scale_image(IMG_PATHS["c3"], SIZES["c3"])
oil_img = load_and_scale_image(IMG_PATHS["oil"], SIZES["oil"])
coolant_img = load_and_scale_image(IMG_PATHS["coolant"], SIZES["coolant"])
engine_img = load_and_scale_image(IMG_PATHS["engine"], SIZES["engine"])
red_bar = load_and_scale_image(IMG_PATHS["red_bar"], SIZES["red_bar"])
orange_bar = load_and_scale_image(IMG_PATHS["orange_bar"], SIZES["orange_bar"])
semi_orange = orange_bar.copy().subsurface((0, int(orange_bar.get_height() / 2), orange_bar.get_width(), int(orange_bar.get_height() / 2)))

logo = load_and_scale_image(IMG_PATHS["logo"], SIZES["logo"])
new_logo = load_and_scale_image(IMG_PATHS["new_logo"], SIZES["new_logo"])

big_font = pygame.font.Font(FONT_PATHS["big"], 80)
small_font = pygame.font.Font(FONT_PATHS["small"], 20)


def draw_dashboard(screen: pygame.Surface, storage: Dict[str, Any], storage_lock: Lock) -> None:
    """Render the dashboard visuals."""
    global v, rp, l, o, c

    screen.fill((0, 0, 0))
    screen_w, screen_h = screen.get_size()

    with storage_lock:
        def checker(data):
            if not isinstance(data, (int, float)):
                return 0
            return int(data)
        speed = checker(storage.get("VEHICLE_SPEED", 0))
        load = checker(storage.get("ENGINE_LOAD", 0))
        rpm = checker(storage.get("ENGINE_SPEED", 0))
        in_press = checker(storage.get("INTAKE_PRESSURE", 0))
        baro = checker(storage.get("BAROMETRIC_PRESSURE", 0))
        coolant = checker(storage.get("ENGINE_COOLANT_TEMP", 0))
        oil = checker(storage.get("ENGINE_OIL_TEMP", 0))

    speed = v
    load = l
    rpm = rp
    coolant = c
    oil = o
    
    boost_kpa = in_press - (baro or 1000)

    if rpm > 1500 and boost_kpa > 15:
        print("TURRBOOOOO")

    screen.blit(bg, get_centered_rect(bg, screen_w, screen_h))
    screen.blit(new_logo, get_centered_rect(new_logo, screen_w, screen_h))
    # screen.blit(logo, get_centered_rect(logo, screen_w, screen_h))
    screen.blit(left, (0, 0))
    screen.blit(right, (screen_w - right.get_width(), 0))
    screen.blit(red_bar, (1125, 61))
    screen.blit(orange_bar, (1145, 99))
    screen.blit(semi_orange, (1157, 137))

    screen.blit(right_group, RIGHT_GROUP_BAR_POS)
    screen.blit(left_group, LEFT_GROUP_BAR_POS)
    screen.blit(left_group_bis, LEFT_GROUP_BAR_POS_BIS)

    screen.blit(oil_img, (275, 290))
    screen.blit(coolant_img, (360, 287))
    screen.blit(engine_img, (980, 295))

    # draw_vertical_bar(screen, left_bar, speed, MAX_SPEED, LEFT_BAR_POS)
    # draw_vertical_bar(screen, right_bar, rpm, MAX_RPM, RIGHT_BAR_POS, piecewise=True)
    # draw_vertical_bar(screen, left_group_bar, oil, MAX_OIL, LEFT_GROUP_BAR_POS)
    # draw_vertical_bar(screen, left_group_bar, coolant, MAX_COOLANT, LEFT_GROUP_BAR_POS_BIS)
    # draw_vertical_bar(screen, right_group_bar, load, MAX_LOAD, RIGHT_GROUP_BAR_POS)

    # draw_speed_text(screen, speed, big_font, SPEED_POS)
    # screen.blit(render_text("km/h", small_font, (255, 255, 255)), KMH_POS)

    # draw_speed_text(screen, rpm, big_font, RPM_POS, 4)
    # screen.blit(render_text("RPM", small_font, (255, 255, 255)), RPM_TEXT_POS)

    screen.blit(render_text(str(MAX_OIL), small_font, (255, 255, 255)), (LEFT_GROUP_BAR_POS[0] + 33, LEFT_GROUP_BAR_POS[1] - 15))
    screen.blit(render_text("0", small_font, (255, 255, 255)), (LEFT_GROUP_BAR_POS[0] + 100, LEFT_GROUP_BAR_POS[1] + 97))

    screen.blit(render_text(str(MAX_COOLANT), small_font, (255, 255, 255)), (LEFT_GROUP_BAR_POS_BIS[0] + 33, LEFT_GROUP_BAR_POS_BIS[1] - 15))
    screen.blit(render_text("0", small_font, (255, 255, 255)), (LEFT_GROUP_BAR_POS_BIS[0] + 100, LEFT_GROUP_BAR_POS_BIS[1] + 97))

    screen.blit(render_text(str(MAX_LOAD), small_font, (255, 255, 255)), (RIGHT_GROUP_BAR_POS[0] + 23, RIGHT_GROUP_BAR_POS[1] - 15))
    screen.blit(render_text("0", small_font, (255, 255, 255)), (RIGHT_GROUP_BAR_POS[0] - 22, RIGHT_GROUP_BAR_POS[1] + 97))

    rpm_labels = ["READY", "0.5", '1', "1.5", '2', '3', '4', '5', '6']
    for i, text in enumerate(rpm_labels):
        x = 1100 + i * 23 if i <= 5 else 1100 + 5 * 23 - (i - 5) * 23 + 10
        y = 355 - i * 39
        screen.blit(render_text(text, small_font, (255, 255, 255)), (x, y))

    speed_labels = [' 0', "20", "40", "60", "80", "100", "120", "140", "160"]
    for i, text in enumerate(speed_labels):
        x = 160 - i * 26 if i <= 5 else 160 - 5 * 26 + (i - 5) * 23 - 10
        y = 355 - i * 39
        screen.blit(render_text(text, small_font, (255, 255, 255)), (x, y))

    pygame.display.flip()

    # Animate mock data
    v = (v + 1) % (MAX_SPEED + 1)
    rp = (rp + 10) % (MAX_RPM + 1)
    l = (l + 1) % (MAX_LOAD + 1)
    c = (c + 1) % (MAX_COOLANT + 1)
    o = (o + 1) % (MAX_OIL + 1)
