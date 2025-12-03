from functools import partial
from typing import Any, Dict

from pygame import Surface
from pygame.font import Font
from pygame.transform import flip

from advanced_logic import DeadReckoningPredictor, Interpolator, SignalFilter, SpringPhysics, IdleSimulator
from config import WIDTH, HEIGHT
from widgets.digit import Digit
from widgets.gauge import Gauge
from widgets.helper import load_scale_image, render_text, safe_int


class Dashboard:
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

    def __init__(self):
        color_white = (255, 255, 255)

        self.big_font = Font(self.FONT_PATHS["big"], 80)
        self.small_font = Font(self.FONT_PATHS["small"], 20)

        self.dashboard = load_scale_image(self.IMG_PATHS["dashboard"], self.SIZES["dashboard"])
        self.left_bar = load_scale_image(self.IMG_PATHS["left_bar"], self.SIZES["left_bar"])
        self.right_bar = flip(self.left_bar.copy(), True, False)
        self.left_group_bar = load_scale_image(self.IMG_PATHS["left_group_bar"], self.SIZES["left_group"])
        self.right_group_bar = flip(self.left_group_bar.copy(), True, False)

        self.label_kmh = render_text(self.small_font, "km/h", color_white)
        self.label_rpm = render_text(self.small_font, "RPM", color_white)

        self._bg_cache = Surface((WIDTH, HEIGHT))
        self._bg_cache.blit(self.dashboard, (0, 0))
        self._bg_cache.blit(self.label_kmh, self.KMH_POS)
        self._bg_cache.blit(self.label_rpm, self.RPM_TEXT_POS)

        self.speed_gauge = Gauge(self.left_bar, self.LEFT_BAR_POS, self.MAX_SPEED)
        rpm_ratio_fn = partial(
            Gauge.gauge_ratio,
            [(0, 0.5), (0.5, 1), (1, 1.5), (1.5, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)],
            [35, 39, 39, 40, 40, 38, 38, 38, 18],
            0.001,
        )
        self.rpm_gauge = Gauge(self.right_bar, self.RIGHT_BAR_POS, self.MAX_RPM, ratio_fn=rpm_ratio_fn)

        self.oil_gauge = Gauge(self.left_group_bar, self.LEFT_GROUP_BAR_POS, self.MAX_OIL)
        self.coolant_gauge = Gauge(self.left_group_bar, self.LEFT_GROUP_BAR_POS_BIS, self.MAX_COOLANT)
        self.load_gauge = Gauge(self.right_group_bar, self.RIGHT_GROUP_BAR_POS, self.MAX_LOAD)

        self.speed_digit = Digit(self.big_font, self.SPEED_POS, 3, color_white, -5)
        self.rpm_digit = Digit(self.big_font, self.RPM_POS, 4, color_white, -5)


        self.speed_filter = SignalFilter(window_size=3)
        self.speed_predictor = DeadReckoningPredictor(max_prediction_time=0.2)
        self.speed_smoother = Interpolator(smoothing_speed=8.0)

        self.rpm_filter = SignalFilter(window_size=1) 
        self.rpm_predictor = DeadReckoningPredictor(max_prediction_time=0.2)
        self.rpm_physics = SpringPhysics(frequency=5.0, damping=0.7)
        self.rpm_idle_sim = IdleSimulator(intensity=20.0, noise_speed=8.0)

    def draw(self, screen: Surface, storage: Dict[str, Any], dt: float) -> None:
        """Render the dashboard."""
        raw_speed = safe_int(storage.get("VEHICLE_SPEED", 0))
        raw_rpm = safe_int(storage.get("ENGINE_SPEED", 0))
        raw_load = safe_int(storage.get("ENGINE_LOAD", 0))
        raw_coolant = safe_int(storage.get("ENGINE_COOLANT_TEMP", 0))

        # raw_rpm = 800

        # oil = safe_int(storage.get("ENGINE_OIL_TEMP", 0))
        # in_press = safe_int(storage.get("INTAKE_PRESSURE", 0))
        # baro = safe_int(storage.get("BAROMETRIC_PRESSURE", 0))

        # boost_kpa = in_press - (baro or 1000)
        # if rpm > 1500 and boost_kpa > 15: 
        #     print("TURRBOOOOO")

        # SPEED
        filtered_speed = self.speed_filter.filter(raw_speed)
        self.speed_predictor.push_update(filtered_speed)
        predicted_speed = self.speed_predictor.get_predicted_value()
        self.speed_smoother.set_target(predicted_speed)
        speed_display = safe_int(self.speed_smoother.update(dt))

        # RPM
        filtered_rpm = self.rpm_filter.filter(raw_rpm)
        self.rpm_predictor.push_update(filtered_rpm)
        predicted_rpm = self.rpm_predictor.get_predicted_value()
        self.rpm_physics.set_target(predicted_rpm)
        rpm_physical = self.rpm_physics.update(dt)
        rpm_display = safe_int(self.rpm_idle_sim.apply(rpm_physical, dt))


        screen.blit(self._bg_cache, (0, 0))

        # self.oil_gauge.draw(screen, oil)
        self.coolant_gauge.draw(screen, raw_coolant)
        self.load_gauge.draw(screen, raw_load)
        self.speed_gauge.draw(screen, speed_display)
        self.rpm_gauge.draw(screen, rpm_display)

        self.speed_digit.draw(screen, speed_display)
        self.rpm_digit.draw(screen, rpm_display)