from functools import partial
from typing import Any, Dict

from pygame import BLEND_MULT, Surface
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

        self.right_bar_ghost = self.right_bar.copy()
        red_tint = Surface(self.right_bar_ghost.get_size())
        red_tint.fill((255, 50, 50))
        self.right_bar_ghost.blit(red_tint, (0, 0), special_flags=BLEND_MULT)
        self.rpm_ghost_gauge = Gauge(self.right_bar_ghost, self.RIGHT_BAR_POS, self.MAX_RPM, ratio_fn=rpm_ratio_fn)

        self.left_bar_ghost = flip(self.right_bar_ghost.copy(), True, False)
        self.speed_ghost_gauge = Gauge(self.left_bar_ghost, self.LEFT_BAR_POS, self.MAX_SPEED)

        self.oil_gauge = Gauge(self.left_group_bar, self.LEFT_GROUP_BAR_POS, self.MAX_OIL)
        self.coolant_gauge = Gauge(self.left_group_bar, self.LEFT_GROUP_BAR_POS_BIS, self.MAX_COOLANT)
        self.load_gauge = Gauge(self.right_group_bar, self.RIGHT_GROUP_BAR_POS, self.MAX_LOAD)

        self.speed_digit = Digit(self.big_font, self.SPEED_POS, 3, color_white, -5)
        self.rpm_digit = Digit(self.big_font, self.RPM_POS, 4, color_white, -5)


        self.speed_filter = SignalFilter(window_size=3)
        self.speed_predictor = DeadReckoningPredictor(max_prediction_time=0.2, max_val=self.MAX_SPEED)
        self.speed_smoother = Interpolator(smoothing_speed=8.0)

        self.speed_ghost_predictor = DeadReckoningPredictor(max_prediction_time=0.5, max_val=self.MAX_SPEED)
        self.speed_ghost_physics = SpringPhysics(frequency=2.0, damping=0.5, max_val=self.MAX_SPEED)

        self.rpm_predictor = DeadReckoningPredictor(max_prediction_time=0.2, max_val=self.MAX_RPM)
        self.rpm_physics = SpringPhysics(frequency=5.0, damping=0.7, max_val=self.MAX_RPM)
        self.rpm_idle_sim = IdleSimulator(intensity=7.5, noise_speed=8.0)

        self.rpm_ghost_predictor = DeadReckoningPredictor(max_prediction_time=0.5, max_val=self.MAX_RPM)
        self.rpm_ghost_physics = SpringPhysics(frequency=2.0, damping=0.5, max_val=self.MAX_RPM)

    def draw(self, screen: Surface, storage: Dict[str, Any], dt: float) -> None:
        """Render the dashboard."""
        # Retrieve raw values, allowing None
        val_speed = storage.get("VEHICLE_SPEED")
        val_rpm = storage.get("ENGINE_SPEED")
        
        raw_load = safe_int(storage.get("ENGINE_LOAD", 0))
        raw_coolant = safe_int(storage.get("ENGINE_COOLANT_TEMP", 0))

        # SPEED
        # Only update predictor if we have a valid reading (not None)
        if val_speed is not None:
            raw_speed = safe_int(val_speed)
            
            # Glitch filter: Ignore sudden 0 if we are moving (> 5 km/h)
            if raw_speed == 0 and self.speed_smoother.current_value > 5:
                pass
            else:
                filtered_speed = self.speed_filter.filter(raw_speed)
                self.speed_predictor.push_update(filtered_speed)
            
        predicted_speed = self.speed_predictor.get_predicted_value()
        self.speed_smoother.set_target(predicted_speed)
        speed_display = safe_int(self.speed_smoother.update(dt))

        # RPM
        # Only update predictor if we have a valid reading (not None)
        if val_rpm is not None:
            raw_rpm = safe_int(val_rpm)
            
            # Glitch filter: Ignore sudden 0 if engine is running (> 400 RPM)
            if raw_rpm == 0 and self.rpm_physics.current_value > 400:
                pass
            else:
                self.rpm_predictor.push_update(raw_rpm)
            
        predicted_rpm = self.rpm_predictor.get_predicted_value()
        self.rpm_physics.set_target(predicted_rpm)
        rpm_physical = self.rpm_physics.update(dt)
        rpm_display = safe_int(self.rpm_idle_sim.apply(rpm_physical, dt))

        DIFF = 50

        self.speed_ghost_predictor.push_update(speed_display)
        predicted_speed_ghost = self.speed_ghost_predictor.get_predicted_value()
        self.speed_ghost_physics.set_target(predicted_speed_ghost)
        speed_ghost_val = self.speed_ghost_physics.update(dt)

        speed_diff = abs(speed_display - speed_ghost_val)
        if speed_diff > DIFF:
            speed_diff = DIFF
        speed_ghost_display = safe_int(speed_display + speed_diff)


        self.rpm_ghost_predictor.push_update(rpm_display)
        predicted_rpm_ghost = self.rpm_ghost_predictor.get_predicted_value()
        self.rpm_ghost_physics.set_target(predicted_rpm_ghost)
        rpm_ghost_val = self.rpm_ghost_physics.update(dt)

        rpm_diff = abs(rpm_display - rpm_ghost_val)
        if rpm_diff > 50:
            rpm_diff = 50
        rpm_ghost_display = safe_int(rpm_display + rpm_diff)


        screen.blit(self._bg_cache, (0, 0))

        # self.oil_gauge.draw(screen, oil)
        self.coolant_gauge.draw(screen, raw_coolant)
        self.load_gauge.draw(screen, raw_load)

        self.speed_ghost_gauge.draw(screen, speed_ghost_display)
        self.speed_gauge.draw(screen, speed_display)

        self.rpm_ghost_gauge.draw(screen, rpm_ghost_display)
        self.rpm_gauge.draw(screen, rpm_display)

        self.speed_digit.draw(screen, speed_display)
        self.rpm_digit.draw(screen, rpm_display)