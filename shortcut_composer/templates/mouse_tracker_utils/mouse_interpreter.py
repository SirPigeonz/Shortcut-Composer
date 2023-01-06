from dataclasses import dataclass

from .new_types import MouseInput, Interpreted


@dataclass
class MouseInterpreter:

    min: Interpreted
    max: Interpreted
    mouse_origin: MouseInput
    start_value: Interpreted
    pixels_in_unit: float

    def interpret(self, mouse: MouseInput) -> Interpreted:
        value = self.start_value + self._delta(mouse)
        self._recalibrate(value)
        return self._clip(value)

    def _recalibrate(self, value: float) -> None:
        delta = (self.min - value)*self.pixels_in_unit
        if delta > 0:
            self.mouse_origin = MouseInput(round(self.mouse_origin - delta))

        delta = (self.max - value)*self.pixels_in_unit
        if delta < 0:
            self.mouse_origin = MouseInput(round(self.mouse_origin - delta))

    def _delta(self, mouse: float) -> float:
        return (mouse - self.mouse_origin)/self.pixels_in_unit

    def _clip(self, value: float) -> Interpreted:
        return Interpreted(min(max(self.min, value), self.max))
