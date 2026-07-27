from functools import partial

from obdii import commands
from pygame import Surface
from pygame.transform import flip

from assets import AssetManager
from config import HEIGHT, WIDTH
from storage import STORAGE_SIGNATURE
from widgets.digit import Digit
from widgets.gauge import Gauge
from widgets.helper import render_text, safe_int
from widgets.interpolation import ValueInterpolator


class Dashboard:
    IMG_PATHS = {
        "dashboard":  "dashboard.png",
        "left_bar":  "left_bar.png",
        "left_group_bar":  "left_group_bar.png",
    }

    SIZES = {
        "dashboard": (1280, 400),
        "left_bar": (130, 325),
        "left_group": (91, 118),
    }

    SPEED_POS = (253, 60)
    KMH_POS = (SPEED_POS[0] + 50, SPEED_POS[1] + 95)
    RPM_POS = (814, 53)
    RPM_TEXT_POS = (RPM_POS[0] + 83, RPM_POS[1] + 95)
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

    def __init__(
        self,
        assets: AssetManager,
        ):
        color_white = (255, 255, 255)

        self.big_font = assets.font("Sarpanch-SemiBold.ttf", 80)
        self.small_font = assets.font("Sarpanch-Regular.ttf", 20)

        self.dashboard = assets.image("dashboard.png", self.SIZES["dashboard"], alpha=False)
        self.left_bar = assets.image("left_bar.png", self.SIZES["left_bar"])
        self.right_bar = flip(self.left_bar.copy(), True, False)
        self.left_group_bar = assets.image("left_group_bar.png", self.SIZES["left_group"])
        self.right_group_bar = flip(self.left_group_bar.copy(), True, False)

        self.label_kmh = render_text(self.small_font, "km/h", color_white)
        self.label_rpm = render_text(self.small_font, "RPM", color_white)

        self._bg_cache = Surface((WIDTH, HEIGHT))
        self._bg_cache.blit(self.dashboard, (0, 0))
        self._bg_cache.blit(self.label_kmh, self.KMH_POS)
        self._bg_cache.blit(self.label_rpm, self.RPM_TEXT_POS)

        rpm_ratio_fn = partial(
            Gauge.gauge_ratio,
            [(0, 0.5), (0.5, 1), (1, 1.5), (1.5, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)],
            [35, 39, 39, 40, 40, 38, 38, 38, 18],
            0.001,
        )

        self.speed_gauge = Gauge(self.left_bar, self.LEFT_BAR_POS, self.MAX_SPEED)
        self.rpm_gauge = Gauge(self.right_bar, self.RIGHT_BAR_POS, self.MAX_RPM, ratio_fn=rpm_ratio_fn)

        self.oil_gauge = Gauge(self.left_group_bar, self.LEFT_GROUP_BAR_POS, self.MAX_OIL)
        self.coolant_gauge = Gauge(self.left_group_bar, self.LEFT_GROUP_BAR_POS_BIS, self.MAX_COOLANT)
        self.load_gauge = Gauge(self.right_group_bar, self.RIGHT_GROUP_BAR_POS, self.MAX_LOAD)

        self.speed_digit = Digit(self.big_font, self.SPEED_POS, 3, color_white, -5)
        self.rpm_digit = Digit(self.big_font, self.RPM_POS, 4, color_white, -5)

        self.speed_interp = ValueInterpolator()
        self.rpm_interp = ValueInterpolator()

    def draw(self, screen: Surface, storage: STORAGE_SIGNATURE, dt: float) -> None:
        """Render the dashboard."""
        speed_raw = safe_int(storage.get(commands["VEHICLE_SPEED"], 0))
        rpm_raw = safe_int(storage.get(commands["ENGINE_SPEED"], 0))
        load_raw = safe_int(storage.get(commands["ENGINE_LOAD"], 0))
        coolant_raw = safe_int(storage.get(commands["ENGINE_COOLANT_TEMP"], 0))

        speed = safe_int(self.speed_interp.update(speed_raw))
        rpm = safe_int(self.rpm_interp.update(rpm_raw))
        # oil = safe_int(storage.get("ENGINE_OIL_TEMP", 0))
        # in_press = safe_int(storage.get("INTAKE_PRESSURE", 0))
        # baro = safe_int(storage.get("BAROMETRIC_PRESSURE", 0))

        # boost_kpa = in_press - (baro or 1000)
        # if rpm > 1500 and boost_kpa > 15: 
        #     print("TURRBOOOOO")

        screen.blit(self._bg_cache, (0, 0))

        # self.oil_gauge.draw(screen, oil)
        self.coolant_gauge.draw(screen, coolant_raw)
        self.load_gauge.draw(screen, load_raw)
        self.speed_gauge.draw(screen, speed)
        self.rpm_gauge.draw(screen, rpm)

        self.speed_digit.draw(screen, speed)
        self.rpm_digit.draw(screen, rpm)