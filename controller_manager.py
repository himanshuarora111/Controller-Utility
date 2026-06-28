from dataclasses import dataclass, field
from typing import List, Tuple

import pygame


@dataclass
class ControllerState:
    connected: bool = False
    name: str = ""
    axes: List[float] = field(default_factory=list)
    buttons: List[int] = field(default_factory=list)
    hats: List[Tuple[int, int]] = field(default_factory=list)
    error: str = ""


class ControllerManager:
    def __init__(self) -> None:
        self.joystick = None
        self.started = False

    def start(self) -> None:
        if self.started:
            return
        pygame.init()
        pygame.joystick.init()
        self.started = True
        self._connect_first()

    def shutdown(self) -> None:
        try:
            if self.joystick:
                self.stop_rumble()
        except Exception:
            pass
        try:
            pygame.joystick.quit()
            pygame.quit()
        except Exception:
            pass
        self.started = False
        self.joystick = None

    def _connect_first(self) -> None:
        try:
            count = pygame.joystick.get_count()
            if count <= 0:
                self.joystick = None
                return
            if self.joystick is None:
                self.joystick = pygame.joystick.Joystick(0)
                self.joystick.init()
        except Exception:
            self.joystick = None

    def poll(self) -> ControllerState:
        if not self.started:
            self.start()

        try:
            pygame.event.pump()
            self._connect_first()

            if self.joystick is None:
                return ControllerState(False)

            name = self.joystick.get_name()
            axes = [self.joystick.get_axis(i) for i in range(self.joystick.get_numaxes())]
            buttons = [self.joystick.get_button(i) for i in range(self.joystick.get_numbuttons())]
            hats = [self.joystick.get_hat(i) for i in range(self.joystick.get_numhats())]

            return ControllerState(True, name, axes, buttons, hats)
        except Exception as exc:
            self.joystick = None
            return ControllerState(False, error=str(exc))

    def rumble(self, low: float, high: float, duration_ms: int) -> tuple[bool, str]:
        if self.joystick is None:
            return False, "No controller connected."
        if not hasattr(self.joystick, "rumble"):
            return False, "This pygame/controller combo does not expose rumble."
        try:
            ok = self.joystick.rumble(float(low), float(high), int(duration_ms))
            if ok:
                return True, "Rumble started."
            return False, "Controller did not accept rumble command."
        except Exception as exc:
            return False, str(exc)

    def stop_rumble(self) -> None:
        if self.joystick is None:
            return
        try:
            if hasattr(self.joystick, "stop_rumble"):
                self.joystick.stop_rumble()
            elif hasattr(self.joystick, "rumble"):
                self.joystick.rumble(0.0, 0.0, 1)
        except Exception:
            pass


def axis_value(state: ControllerState, index: int, default: float = 0.0) -> float:
    if 0 <= index < len(state.axes):
        return float(state.axes[index])
    return default


def button_value(state: ControllerState, index: int) -> int:
    if 0 <= index < len(state.buttons):
        return int(state.buttons[index])
    return 0


def hat_value(state: ControllerState, index: int = 0) -> tuple[int, int]:
    if 0 <= index < len(state.hats):
        return state.hats[index]
    return (0, 0)
