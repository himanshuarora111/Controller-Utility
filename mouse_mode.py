import subprocess
import time
from typing import Dict, Set

from pynput.keyboard import Controller as KeyboardController
from pynput.keyboard import Key
from pynput.mouse import Button, Controller as MouseController

from controller_manager import ControllerState, axis_value, button_value, hat_value


BUTTON_A = 0
BUTTON_B = 1
BUTTON_X = 2
BUTTON_Y = 3
BUTTON_LB = 4
BUTTON_RB = 5
BUTTON_VIEW = 6
BUTTON_MENU = 7

AXIS_LEFT_X = 0
AXIS_LEFT_Y = 1
AXIS_RIGHT_X = 2
AXIS_RIGHT_Y = 3
AXIS_LT = 4
AXIS_RT = 5


class MouseMode:
    def __init__(self, max_speed: float = 14.0, deadzone: float = 0.15) -> None:
        self.enabled = False
        self.max_speed = float(max_speed)
        self.deadzone = float(deadzone)
        self.mouse = MouseController()
        self.keyboard = KeyboardController()
        self.prev_buttons: Dict[int, int] = {}
        self.held_keys: Set[Key] = set()
        self.left_mouse_down = False
        self.right_mouse_down = False
        self.last_scroll_time = 0.0
        self.scroll_interval = 0.055

    def start(self) -> None:
        self.enabled = True
        self._wake_cursor()

    def stop(self) -> None:
        self.enabled = False
        self.release_all()

    def set_speed(self, max_speed: float) -> None:
        self.max_speed = float(max_speed)

    def set_deadzone(self, deadzone: float) -> None:
        self.deadzone = float(deadzone)

    def release_all(self) -> None:
        try:
            if self.left_mouse_down:
                self.mouse.release(Button.left)
            if self.right_mouse_down:
                self.mouse.release(Button.right)
        except Exception:
            pass
        self.left_mouse_down = False
        self.right_mouse_down = False

        for key in list(self.held_keys):
            try:
                self.keyboard.release(key)
            except Exception:
                pass
        self.held_keys.clear()
        self.prev_buttons.clear()

    def update(self, state: ControllerState) -> None:
        if not self.enabled or not state.connected:
            return

        self._handle_mouse_move(state)
        self._handle_scroll(state)
        self._handle_buttons(state)
        self._handle_dpad(state)
        self._save_previous_buttons(state)

    def _curve(self, value: float) -> float:
        if abs(value) < self.deadzone:
            return 0.0
        sign = 1.0 if value >= 0 else -1.0
        normalized = (abs(value) - self.deadzone) / max(0.01, 1.0 - self.deadzone)
        return sign * (normalized ** 2)

    def _trigger_pressed(self, value: float) -> bool:
        # Works for both 0..1 and -1..1 trigger ranges.
        return value > 0.25

    def _handle_mouse_move(self, state: ControllerState) -> None:
        x = self._curve(axis_value(state, AXIS_LEFT_X))
        y = self._curve(axis_value(state, AXIS_LEFT_Y))

        lt = axis_value(state, AXIS_LT, -1.0)
        rt = axis_value(state, AXIS_RT, -1.0)

        speed = self.max_speed
        if self._trigger_pressed(rt):
            speed *= 0.35
        if self._trigger_pressed(lt):
            speed *= 1.8

        dx = int(x * speed)
        dy = int(y * speed)
        if dx or dy:
            self.mouse.move(dx, dy)

    def _handle_scroll(self, state: ControllerState) -> None:
        now = time.time()
        if now - self.last_scroll_time < self.scroll_interval:
            return

        sx = self._curve(axis_value(state, AXIS_RIGHT_X))
        sy = self._curve(axis_value(state, AXIS_RIGHT_Y))
        scroll_x = int(sx * 3)
        scroll_y = int(-sy * 3)

        if scroll_x or scroll_y:
            try:
                self.mouse.scroll(scroll_x, scroll_y)
            except Exception:
                pass
            self.last_scroll_time = now

    def _handle_buttons(self, state: ControllerState) -> None:
        a = button_value(state, BUTTON_A)
        b = button_value(state, BUTTON_B)

        if a and not self.prev_buttons.get(BUTTON_A, 0):
            self.mouse.press(Button.left)
            self.left_mouse_down = True
        if not a and self.prev_buttons.get(BUTTON_A, 0):
            self.mouse.release(Button.left)
            self.left_mouse_down = False

        if b and not self.prev_buttons.get(BUTTON_B, 0):
            self.mouse.press(Button.right)
            self.right_mouse_down = True
        if not b and self.prev_buttons.get(BUTTON_B, 0):
            self.mouse.release(Button.right)
            self.right_mouse_down = False

        if self._pressed_now(state, BUTTON_Y):
            self._launch_touch_keyboard()

        if self._pressed_now(state, BUTTON_RB):
            self._tap_key(Key.esc)

        if self._pressed_now(state, BUTTON_MENU):
            self._tap_key(Key.enter)

    def _handle_dpad(self, state: ControllerState) -> None:
        hx, hy = hat_value(state)
        wanted: Set[Key] = set()
        if hx < 0:
            wanted.add(Key.left)
        elif hx > 0:
            wanted.add(Key.right)
        if hy > 0:
            wanted.add(Key.up)
        elif hy < 0:
            wanted.add(Key.down)

        for key in list(self.held_keys):
            if key not in wanted:
                try:
                    self.keyboard.release(key)
                except Exception:
                    pass
                self.held_keys.discard(key)

        for key in wanted:
            if key not in self.held_keys:
                try:
                    self.keyboard.press(key)
                    self.held_keys.add(key)
                except Exception:
                    pass

    def _pressed_now(self, state: ControllerState, button_index: int) -> bool:
        current = button_value(state, button_index)
        previous = self.prev_buttons.get(button_index, 0)
        return bool(current and not previous)

    def _save_previous_buttons(self, state: ControllerState) -> None:
        self.prev_buttons = {i: int(v) for i, v in enumerate(state.buttons)}

    def _tap_key(self, key: Key) -> None:
        try:
            self.keyboard.press(key)
            self.keyboard.release(key)
        except Exception:
            pass

    def _wake_cursor(self) -> None:
        try:
            self.mouse.move(1, 0)
            self.mouse.move(-1, 0)
        except Exception:
            pass

    def _launch_touch_keyboard(self) -> None:
        try:
            subprocess.Popen('cmd /c start "" "tabtip.exe"', shell=True)
        except Exception:
            try:
                subprocess.Popen("osk.exe", shell=True)
            except Exception:
                pass
