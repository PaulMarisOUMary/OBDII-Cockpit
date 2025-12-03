from functools import reduce
from math import gcd
from typing import Dict, List

from obdii import Command


def lcm(a: int, b: int) -> int:
    return a * b // gcd(a, b)


def lcm_list(numbers: List[int]) -> int:
    return reduce(lcm, numbers) if numbers else 1


class PollingManager:
    def __init__(self) -> None:
        self.command_list: Dict[Command, int] = {}

        self.cycle_count = 0
        self._wrap_at = 1

    def register(self, command: Command, frequency: int) -> None:
        self.command_list[command] = frequency

        self._wrap_at = lcm_list(list(self.command_list.values()))

    def get_cycle(self) -> List[Command]:
        result = [
            cmd
            for cmd, freq in self.command_list.items()
            if self.cycle_count % freq == 0
        ]

        self.cycle_count += 1
        if self.cycle_count >= self._wrap_at:
            self.cycle_count = 0

        return result