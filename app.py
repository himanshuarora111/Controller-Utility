import sys
from typing import Dict

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QHeaderView,
)

import startup
from combos import COMBOS
from controller_manager import ControllerManager, ControllerState
from mouse_mode import MouseMode
from settings import load_settings, save_settings


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Controller Utility")
        self.resize(940, 620)

        self.settings: Dict = load_settings()
        self.controller = ControllerManager()
        self.controller.start()
        self.state = ControllerState(False)

        self.mouse_mode = MouseMode(
            max_speed=self.settings.get("mouse_max_speed", 14),
            deadzone=self.settings.get("mouse_deadzone", 0.15),
        )

        self.continuous_vibration = False
        self.ui_tick_count = 0

        self._build_ui()
        self._load_startup_checkbox()

        if self.settings.get("auto_start_mouse_mode", False):
            self.mouse_mode.start()

        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self._tick)
        self.poll_timer.start(16)

        self.vibe_timer = QTimer(self)
        self.vibe_timer.timeout.connect(self._repeat_vibration)

        self._update_all_labels()

    def _build_ui(self) -> None:
        tabs = QTabWidget()
        tabs.addTab(self._home_tab(), "Home")
        tabs.addTab(self._mouse_tab(), "Mouse Mode")
        tabs.addTab(self._vibration_tab(), "Vibration")
        tabs.addTab(self._combos_tab(), "Combos")
        self.setCentralWidget(tabs)

    def _home_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        status_box = QGroupBox("Status")
        grid = QGridLayout(status_box)
        self.connected_label = QLabel("No")
        self.controller_name_label = QLabel("-")
        self.mouse_status_label = QLabel("Off")
        self.startup_status_label = QLabel("Off")
        self.axis_count_label = QLabel("0")
        self.button_count_label = QLabel("0")

        grid.addWidget(QLabel("Controller connected:"), 0, 0)
        grid.addWidget(self.connected_label, 0, 1)
        grid.addWidget(QLabel("Controller name:"), 1, 0)
        grid.addWidget(self.controller_name_label, 1, 1)
        grid.addWidget(QLabel("Mouse mode:"), 2, 0)
        grid.addWidget(self.mouse_status_label, 2, 1)
        grid.addWidget(QLabel("Start with Windows:"), 3, 0)
        grid.addWidget(self.startup_status_label, 3, 1)
        grid.addWidget(QLabel("Axes detected:"), 4, 0)
        grid.addWidget(self.axis_count_label, 4, 1)
        grid.addWidget(QLabel("Buttons detected:"), 5, 0)
        grid.addWidget(self.button_count_label, 5, 1)

        live_box = QGroupBox("Live input")
        live_layout = QVBoxLayout(live_box)
        self.live_input_text = QTextEdit()
        self.live_input_text.setReadOnly(True)
        self.live_input_text.setMinimumHeight(180)
        live_layout.addWidget(self.live_input_text)

        layout.addWidget(status_box)
        layout.addWidget(live_box)
        layout.addStretch(1)
        return page

    def _mouse_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        self.mouse_toggle_button = QPushButton("Start Mouse Mode")
        self.mouse_toggle_button.clicked.connect(self._toggle_mouse_mode)

        self.auto_start_mouse_checkbox = QCheckBox("Start Mouse Mode when this app opens")
        self.auto_start_mouse_checkbox.setChecked(bool(self.settings.get("auto_start_mouse_mode", False)))
        self.auto_start_mouse_checkbox.toggled.connect(self._on_auto_start_mouse_changed)

        self.startup_checkbox = QCheckBox("Start this app with Windows")
        self.startup_checkbox.toggled.connect(self._on_startup_toggled)

        speed_row = QHBoxLayout()
        self.speed_label = QLabel(str(int(self.settings.get("mouse_max_speed", 14))))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(4)
        self.speed_slider.setMaximum(40)
        self.speed_slider.setValue(int(self.settings.get("mouse_max_speed", 14)))
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        speed_row.addWidget(QLabel("Mouse speed"))
        speed_row.addWidget(self.speed_slider)
        speed_row.addWidget(self.speed_label)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setText(
            "Current controls:\n"
            "Left stick = move mouse\n"
            "Right stick = scroll\n"
            "A = hold left click / drag\n"
            "B = hold right click\n"
            "RT = precision slow mode\n"
            "LT = fast mode\n"
            "Y = open touch keyboard\n"
            "RB = Escape\n"
            "Menu/Start = Enter\n"
            "D-pad = arrow keys"
        )

        layout.addWidget(self.mouse_toggle_button)
        layout.addWidget(self.auto_start_mouse_checkbox)
        layout.addWidget(self.startup_checkbox)
        layout.addLayout(speed_row)
        layout.addWidget(help_text)
        return page

    def _vibration_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        low_value = int(float(self.settings.get("last_vibration_low", 0.5)) * 100)
        high_value = int(float(self.settings.get("last_vibration_high", 0.5)) * 100)

        self.low_slider, self.low_value_label = self._make_slider(low_value)
        self.high_slider, self.high_value_label = self._make_slider(high_value)

        self.duration_spin = QSpinBox()
        self.duration_spin.setMinimum(100)
        self.duration_spin.setMaximum(10000)
        self.duration_spin.setSingleStep(100)
        self.duration_spin.setValue(int(self.settings.get("last_vibration_duration_ms", 1000)))

        layout.addLayout(self._slider_row("Low frequency motor", self.low_slider, self.low_value_label))
        layout.addLayout(self._slider_row("High frequency motor", self.high_slider, self.high_value_label))

        duration_row = QHBoxLayout()
        duration_row.addWidget(QLabel("Duration ms"))
        duration_row.addWidget(self.duration_spin)
        duration_row.addStretch(1)
        layout.addLayout(duration_row)

        button_row = QHBoxLayout()
        test_btn = QPushButton("Test once")
        test_btn.clicked.connect(self._test_vibration_once)
        self.continuous_btn = QPushButton("Start continuous")
        self.continuous_btn.clicked.connect(self._toggle_continuous_vibration)
        stop_btn = QPushButton("Stop vibration")
        stop_btn.clicked.connect(self._stop_vibration)
        button_row.addWidget(test_btn)
        button_row.addWidget(self.continuous_btn)
        button_row.addWidget(stop_btn)
        layout.addLayout(button_row)

        self.vibration_status_label = QLabel("Ready.")
        layout.addWidget(self.vibration_status_label)
        layout.addStretch(1)
        return page

    def _combos_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        note = QLabel("This tab is a cheat sheet. It does not send these combos to the controller yet.")
        note.setWordWrap(True)
        layout.addWidget(note)

        table = QTableWidget(len(COMBOS), 4)
        table.setHorizontalHeaderLabels(["Type", "Feature", "Combo", "Notes"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)

        for row, item in enumerate(COMBOS):
            table.setItem(row, 0, QTableWidgetItem(item["type"]))
            table.setItem(row, 1, QTableWidgetItem(item["feature"]))
            table.setItem(row, 2, QTableWidgetItem(item["combo"]))
            table.setItem(row, 3, QTableWidgetItem(item["notes"]))

        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        layout.addWidget(table)
        return page

    def _make_slider(self, value: int):
        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(0)
        slider.setMaximum(100)
        slider.setValue(value)
        label = QLabel(f"{value}%")
        slider.valueChanged.connect(lambda v, target=label: target.setText(f"{v}%"))
        slider.valueChanged.connect(lambda _v: self._save_vibration_settings())
        return slider, label

    def _slider_row(self, title: str, slider: QSlider, label: QLabel) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addWidget(QLabel(title))
        row.addWidget(slider)
        row.addWidget(label)
        return row

    def _tick(self) -> None:
        self.state = self.controller.poll()
        if self.mouse_mode.enabled:
            self.mouse_mode.update(self.state)

        self.ui_tick_count += 1
        if self.ui_tick_count >= 15:
            self.ui_tick_count = 0
            self._update_all_labels()

    def _update_all_labels(self) -> None:
        connected = self.state.connected
        self.connected_label.setText("Yes" if connected else "No")
        self.controller_name_label.setText(self.state.name if connected else "-")
        self.mouse_status_label.setText("On" if self.mouse_mode.enabled else "Off")
        self.axis_count_label.setText(str(len(self.state.axes)) if connected else "0")
        self.button_count_label.setText(str(len(self.state.buttons)) if connected else "0")
        self.mouse_toggle_button.setText("Stop Mouse Mode" if self.mouse_mode.enabled else "Start Mouse Mode")

        if connected:
            active_buttons = [str(i) for i, v in enumerate(self.state.buttons) if v]
            axes = "  ".join(f"A{i}: {v:+.2f}" for i, v in enumerate(self.state.axes))
            hats = "  ".join(f"H{i}: {v}" for i, v in enumerate(self.state.hats)) or "none"
            buttons = ", ".join(active_buttons) if active_buttons else "none"
            self.live_input_text.setPlainText(
                f"Controller: {self.state.name}\n\n"
                f"Axes:\n{axes}\n\n"
                f"Pressed buttons:\n{buttons}\n\n"
                f"Hats / D-pad:\n{hats}"
            )
        else:
            error = f"\nError: {self.state.error}" if self.state.error else ""
            self.live_input_text.setPlainText(f"No controller connected.{error}")

        try:
            self.startup_status_label.setText("On" if startup.is_startup_enabled() else "Off")
        except Exception:
            self.startup_status_label.setText("Unavailable")

    def _toggle_mouse_mode(self) -> None:
        if self.mouse_mode.enabled:
            self.mouse_mode.stop()
        else:
            self.mouse_mode.start()
        self._update_all_labels()

    def _on_auto_start_mouse_changed(self, checked: bool) -> None:
        self.settings["auto_start_mouse_mode"] = bool(checked)
        save_settings(self.settings)

    def _load_startup_checkbox(self) -> None:
        try:
            self.startup_checkbox.blockSignals(True)
            self.startup_checkbox.setChecked(startup.is_startup_enabled())
            self.startup_checkbox.blockSignals(False)
        except Exception:
            self.startup_checkbox.setEnabled(False)
            self.startup_checkbox.setText("Start this app with Windows (Windows only)")

    def _on_startup_toggled(self, checked: bool) -> None:
        try:
            if checked:
                startup.enable_startup()
            else:
                startup.disable_startup()
        except Exception as exc:
            QMessageBox.warning(self, "Startup error", str(exc))
        self._update_all_labels()

    def _on_speed_changed(self, value: int) -> None:
        self.speed_label.setText(str(value))
        self.mouse_mode.set_speed(value)
        self.settings["mouse_max_speed"] = value
        save_settings(self.settings)

    def _vibration_values(self) -> tuple[float, float, int]:
        low = self.low_slider.value() / 100.0
        high = self.high_slider.value() / 100.0
        duration = int(self.duration_spin.value())
        return low, high, duration

    def _save_vibration_settings(self) -> None:
        low, high, duration = self._vibration_values()
        self.settings["last_vibration_low"] = low
        self.settings["last_vibration_high"] = high
        self.settings["last_vibration_duration_ms"] = duration
        save_settings(self.settings)

    def _test_vibration_once(self) -> None:
        self._save_vibration_settings()
        low, high, duration = self._vibration_values()
        ok, msg = self.controller.rumble(low, high, duration)
        self.vibration_status_label.setText(msg)
        if not ok:
            QMessageBox.information(self, "Vibration", msg)

    def _toggle_continuous_vibration(self) -> None:
        if self.continuous_vibration:
            self._stop_vibration()
            return
        self.continuous_vibration = True
        self.continuous_btn.setText("Stop continuous")
        self._repeat_vibration()
        self.vibe_timer.start(850)

    def _repeat_vibration(self) -> None:
        low, high, _duration = self._vibration_values()
        ok, msg = self.controller.rumble(low, high, 1000)
        self.vibration_status_label.setText(msg)
        if not ok:
            self._stop_vibration()

    def _stop_vibration(self) -> None:
        self.continuous_vibration = False
        self.vibe_timer.stop()
        self.controller.stop_rumble()
        self.continuous_btn.setText("Start continuous")
        self.vibration_status_label.setText("Vibration stopped.")

    def closeEvent(self, event) -> None:
        self._stop_vibration()
        self.mouse_mode.stop()
        self.controller.shutdown()
        save_settings(self.settings)
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
