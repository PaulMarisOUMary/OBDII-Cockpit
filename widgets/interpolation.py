from time import monotonic
from typing import Optional


class ValueInterpolator:
    SNAP_RATIO_THRESHOLD = 4.0
    _INTERVAL_EMA_ALPHA = 0.2

    def __init__(self) -> None:
        self._has_value = False
        self._raw_value: float = 0.0

        self._start_value: float = 0.0
        self._target_value: float = 0.0
        self._start_time: float = monotonic()
        self._duration: float = 0.0

        self._last_sample_time: float = monotonic()
        self._avg_interval: Optional[float] = None

    def update(self, raw_value: float) -> float:
        now = monotonic()

        if not self._has_value or raw_value != self._raw_value:
            self._on_new_sample(raw_value, now)

        return self._value_at(now)

    def _on_new_sample(self, raw_value: float, now: float) -> None:
        interval = now - self._last_sample_time
        self._last_sample_time = now

        if not self._has_value:
            self._start_value = raw_value
            self._duration = 0.0
        else:
            current_displayed = self._value_at(now)
            is_break = (
                self._avg_interval is not None
                and interval > self.SNAP_RATIO_THRESHOLD * self._avg_interval
            )

            if is_break:
                self._start_value = raw_value
                self._duration = 0.0
            else:
                self._start_value = current_displayed
                self._duration = interval
                self._avg_interval = (
                    interval if self._avg_interval is None
                    else self._avg_interval * (1 - self._INTERVAL_EMA_ALPHA)
                    + interval * self._INTERVAL_EMA_ALPHA
                )

        self._target_value = raw_value
        self._start_time = now
        self._raw_value = raw_value
        self._has_value = True

    def _value_at(self, now: float) -> float:
        if self._duration <= 0:
            return self._target_value

        t = (now - self._start_time) / self._duration
        if t >= 1.0:
            return self._target_value

        return self._start_value + (self._target_value - self._start_value) * t