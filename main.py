"""
Kitty Egg Timer — Main Application
====================================
Premium animated egg timer desktop app with a cute kitty mascot.
"""

import sys
import json
from pathlib import Path

from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    pyqtProperty, QRectF,
)
from PyQt6.QtGui import (
    QColor, QPainter, QBrush, QPen, QFont,
    QLinearGradient, QPainterPath, QRadialGradient,
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSpinBox, QGraphicsDropShadowEffect,
)

from utils.theme import (
    BG_COLOR, BG_HEX, CARD_SURFACE, CARD_HEX, CARD_HOVER_HEX,
    ACCENT_PINK, ACCENT_PINK_HEX, SOFT_BLUE, SOFT_BLUE_HEX,
    SUCCESS_MINT, SUCCESS_MINT_HEX, DANGER_RED, DANGER_RED_HEX,
    TEXT_PRIMARY, TEXT_PRIMARY_HEX, TEXT_SECONDARY, TEXT_SECONDARY_HEX,
    CORNER_RADIUS, CARD_PADDING, WINDOW_WIDTH, WINDOW_HEIGHT,
    SHADOW_BLUR, SHADOW_OFFSET_Y, SHADOW_COLOR,
    heading_font, body_font,
)
# Note: we do NOT use fade_in (QGraphicsOpacityEffect) on the main window
# because it conflicts with child widgets that have QGraphicsDropShadowEffect.
# Instead we animate windowOpacity directly.
from utils.sound_manager import SoundManager

from widgets.kitty_widget import KittyWidget
from widgets.timer_ring import TimerRing
from widgets.particle_system import ParticleSystem
from widgets.animated_button import AnimatedButton


# ── Settings persistence ────────────────────────────────────────────────
SETTINGS_PATH = Path.home() / ".kitty_timer_settings.json"


def _load_settings() -> dict:
    try:
        return json.loads(SETTINGS_PATH.read_text())
    except Exception:
        return {"last_minutes": 5}


def _save_settings(data: dict):
    try:
        SETTINGS_PATH.write_text(json.dumps(data, indent=2))
    except Exception:
        pass


# ── Timer States ────────────────────────────────────────────────────────
IDLE = "idle"
RUNNING = "running"
PAUSED = "paused"
COMPLETED = "completed"


# ── Background Glow Overlay ────────────────────────────────────────────
class BackgroundGlow(QWidget):
    """Animated radial glow behind the card on completion."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._opacity = 0.0

        self._anim = QPropertyAnimation(self, b"glow_opacity", self)
        self._anim.setDuration(1200)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutSine)

    @pyqtProperty(float)
    def glow_opacity(self):
        return self._opacity

    @glow_opacity.setter
    def glow_opacity(self, v):
        self._opacity = v
        self.update()

    def pulse(self):
        self._anim.stop()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(0.7)
        self._anim.setDuration(600)
        self._anim.setLoopCount(1)
        try:
            self._anim.finished.disconnect(self._fade_out)
        except TypeError:
            pass
        self._anim.finished.connect(self._fade_out)
        self._anim.start()

    def _fade_out(self):
        try:
            self._anim.finished.disconnect(self._fade_out)
        except TypeError:
            pass
        self._anim.setStartValue(self._opacity)
        self._anim.setEndValue(0.0)
        self._anim.setDuration(1800)
        self._anim.setLoopCount(1)
        self._anim.start()

    def reset(self):
        self._anim.stop()
        self._opacity = 0.0
        self.update()

    def paintEvent(self, event):
        if self._opacity < 0.01:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() / 2, self.height() * 0.4
        grad = QRadialGradient(cx, cy, max(cx, cy))
        grad.setColorAt(0.0, QColor(255, 111, 174, int(self._opacity * 90)))
        grad.setColorAt(0.35, QColor(127, 219, 255, int(self._opacity * 45)))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(grad))
        p.drawRect(self.rect())
        p.end()


# ═══════════════════════════════════════════════════════════════════════
#  SPINBOX STYLESHEET
# ═══════════════════════════════════════════════════════════════════════
SPINBOX_STYLE = f"""
QSpinBox {{
    background: {BG_HEX};
    color: {TEXT_PRIMARY_HEX};
    border: 2px solid #3A3A3C;
    border-radius: 10px;
    padding: 4px 10px;
    font-size: 14px;
    font-weight: bold;
    font-family: 'SF Mono', 'Menlo', monospace;
    min-width: 60px;
}}
QSpinBox:focus {{
    border: 2px solid {ACCENT_PINK_HEX};
    background: #3A3A3C;
}}
QSpinBox::up-button, QSpinBox::down-button {{
    width: 18px;
    background: transparent;
    border: none;
}}
QSpinBox::up-arrow {{
    image: none;
    width: 0; height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 5px solid {TEXT_SECONDARY_HEX};
}}
QSpinBox::down-arrow {{
    image: none;
    width: 0; height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {TEXT_SECONDARY_HEX};
}}
"""


# ═══════════════════════════════════════════════════════════════════════
#  MAIN WINDOW
# ═══════════════════════════════════════════════════════════════════════
class KittyTimerApp(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kitty Egg Timer")
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.Window
        )

        self._state = IDLE
        self._total_seconds = 0
        self._remaining_seconds = 0
        self._drag_pos = None
        self._tick_counter = 0

        # Sound
        self._sound = SoundManager()
        self._sound.init()

        # Load settings
        settings = _load_settings()
        self._last_minutes = settings.get("last_minutes", 5)

        # ── Central widget ──────────────────────────────────────────────
        central = QWidget(self)
        self.setCentralWidget(central)
        central.setStyleSheet("background: transparent;")

        self._main_layout = QVBoxLayout(central)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # ── Card surface ────────────────────────────────────────────────
        self._card = QWidget(central)
        self._card.setObjectName("card")
        self._card.setStyleSheet(f"""
            #card {{
                background-color: {CARD_HEX};
                border-radius: {CORNER_RADIUS}px;
            }}
        """)
        self._main_layout.addWidget(self._card)

        card_layout = QVBoxLayout(self._card)
        card_layout.setContentsMargins(
            CARD_PADDING, CARD_PADDING, CARD_PADDING, CARD_PADDING
        )
        card_layout.setSpacing(10)

        # ── Title bar (drag area) ───────────────────────────────────────
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(0, 0, 0, 0)

        # Close button (traffic-light style)
        close_btn = AnimatedButton("✕", accent=DANGER_RED, parent=self._card)
        close_btn.setFixedSize(28, 28)
        close_btn.setFont(QFont("SF Pro Display", 12, QFont.Weight.Bold))
        close_btn.clicked.connect(self.close)
        title_bar.addWidget(close_btn)

        title_bar.addStretch()

        self._title_label = QLabel("🐱  Kitty Egg Timer")
        self._title_label.setFont(heading_font(16))
        self._title_label.setStyleSheet(f"color: {TEXT_SECONDARY_HEX}; background: transparent;")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_bar.addWidget(self._title_label)

        title_bar.addStretch()

        # Spacer to balance close button
        spacer_w = QWidget()
        spacer_w.setFixedSize(28, 28)
        spacer_w.setStyleSheet("background: transparent;")
        title_bar.addWidget(spacer_w)

        card_layout.addLayout(title_bar)

        # ── Kitty + Ring composite ──────────────────────────────────────
        ring_container = QWidget()
        ring_container.setFixedSize(280, 280)
        ring_container.setStyleSheet("background: transparent;")

        self._ring = TimerRing(ring_container)
        self._ring.move(0, 0)

        self._kitty = KittyWidget(ring_container)
        self._kitty.move(
            (280 - self._kitty.width()) // 2,
            (280 - self._kitty.height()) // 2 - 10,
        )

        ring_row = QHBoxLayout()
        ring_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ring_row.addWidget(ring_container)
        card_layout.addLayout(ring_row)

        # ── Status label ────────────────────────────────────────────────
        self._status_label = QLabel("Pick your egg 🥚")
        self._status_label.setFont(body_font(13, bold=True))
        self._status_label.setStyleSheet(
            f"color: {TEXT_SECONDARY_HEX}; background: transparent;"
        )
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self._status_label)

        # ── Preset buttons ──────────────────────────────────────────────
        presets_row = QHBoxLayout()
        presets_row.setSpacing(8)

        for label, minutes, color in [
            ("🥚 Soft  5m", 5, QColor("#FFD700")),
            ("🥚 Medium  7m", 7, QColor(SOFT_BLUE)),
            ("🥚 Hard  10m", 10, QColor(ACCENT_PINK)),
        ]:
            btn = AnimatedButton(label, accent=color, parent=self._card)
            btn.clicked.connect(lambda checked, m=minutes: self._set_time(m))
            presets_row.addWidget(btn)

        card_layout.addLayout(presets_row)

        # ── Custom input ────────────────────────────────────────────────
        custom_row = QHBoxLayout()
        custom_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        custom_row.setSpacing(8)

        custom_label = QLabel("Custom:")
        custom_label.setFont(body_font(12))
        custom_label.setStyleSheet(f"color: {TEXT_SECONDARY_HEX}; background: transparent;")
        custom_row.addWidget(custom_label)

        self._spin = QSpinBox(self._card)
        self._spin.setRange(1, 120)
        self._spin.setValue(self._last_minutes)
        self._spin.setSuffix(" min")
        self._spin.setFixedSize(100, 36)
        self._spin.setStyleSheet(SPINBOX_STYLE)
        custom_row.addWidget(self._spin)

        custom_set_btn = AnimatedButton("Set", accent=ACCENT_PINK, parent=self._card)
        custom_set_btn.setFixedWidth(65)
        custom_set_btn.clicked.connect(
            lambda: self._set_time(self._spin.value())
        )
        custom_row.addWidget(custom_set_btn)

        card_layout.addLayout(custom_row)
        card_layout.addSpacing(4)

        # ── Control buttons ─────────────────────────────────────────────
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(10)

        self._start_btn = AnimatedButton(
            "Start", accent=SUCCESS_MINT, parent=self._card, icon_text="▶"
        )
        self._start_btn.clicked.connect(self._toggle_start_pause)
        ctrl_row.addWidget(self._start_btn)

        self._reset_btn = AnimatedButton(
            "Reset", accent=DANGER_RED, parent=self._card, icon_text="↺"
        )
        self._reset_btn.clicked.connect(self._reset)
        ctrl_row.addWidget(self._reset_btn)

        card_layout.addLayout(ctrl_row)
        card_layout.addStretch()

        # ── Overlay layers ──────────────────────────────────────────────
        self._bg_glow = BackgroundGlow(self)
        self._bg_glow.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self._bg_glow.move(0, 0)
        self._bg_glow.lower()

        self._particles = ParticleSystem(self)
        self._particles.move(0, 0)
        self._particles.raise_()

        # ── Core timer (50ms ticks) ─────────────────────────────────────
        self._tick_timer = QTimer(self)
        self._tick_timer.setInterval(50)
        self._tick_timer.timeout.connect(self._tick)

        # ── Window fade-in (via windowOpacity — no QGraphicsEffect) ────
        self.setWindowOpacity(0.0)
        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(600)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._fade.start()

        # Initialise ring display
        self._set_time(self._last_minutes)

    # ── Time setting ────────────────────────────────────────────────────
    def _set_time(self, minutes: int):
        if self._state == RUNNING:
            return
        self._total_seconds = minutes * 60
        self._remaining_seconds = self._total_seconds
        self._last_minutes = minutes
        self._update_display()
        self._ring.progress = 1.0
        self._ring.set_warning(False)
        self._state = IDLE
        self._spin.setValue(minutes)
        self._start_btn.setText("Start")
        self._status_label.setText(
            f"Ready: {minutes} minute{'s' if minutes != 1 else ''} 🐾"
        )
        _save_settings({"last_minutes": minutes})

    # ── Start / Pause toggle ────────────────────────────────────────────
    def _toggle_start_pause(self):
        if self._state in (IDLE, COMPLETED):
            # Start
            if self._state == COMPLETED:
                self._remaining_seconds = self._total_seconds
                self._ring.reset()
                self._particles.clear()
                self._bg_glow.reset()
            self._state = RUNNING
            self._tick_counter = 0
            self._kitty.set_running(True)
            self._tick_timer.start()
            self._start_btn.setText("Pause")
            self._status_label.setText("Cooking… 🍳")
        elif self._state == RUNNING:
            # Pause
            self._state = PAUSED
            self._tick_timer.stop()
            self._kitty.set_running(False)
            self._start_btn.setText("Resume")
            self._status_label.setText("Paused ⏸")
        elif self._state == PAUSED:
            # Resume
            self._state = RUNNING
            self._kitty.set_running(True)
            self._tick_timer.start()
            self._start_btn.setText("Pause")
            self._status_label.setText("Cooking… 🍳")

    # ── Reset ───────────────────────────────────────────────────────────
    def _reset(self):
        self._tick_timer.stop()
        self._state = IDLE
        self._remaining_seconds = self._total_seconds
        self._tick_counter = 0
        self._kitty.set_running(False)
        self._ring.reset()
        self._ring.set_warning(False)
        self._particles.clear()
        self._bg_glow.reset()
        self._update_display()
        self._start_btn.setText("Start")
        self._status_label.setText("Pick your egg 🥚")

    # ── Tick (50ms) ─────────────────────────────────────────────────────
    def _tick(self):
        self._tick_counter += 1

        # Decrement every second (50ms × 20 = 1000ms)
        if self._tick_counter >= 20:
            self._tick_counter = 0
            self._remaining_seconds = max(0, self._remaining_seconds - 1)

            # Tick sound in last 5 seconds
            if 0 < self._remaining_seconds <= 5:
                self._sound.play_tick()

        # Update display
        self._update_display()

        # Progress
        if self._total_seconds > 0:
            self._ring.progress = self._remaining_seconds / self._total_seconds

        # Warning (last 10 seconds)
        self._ring.set_warning(
            self._state == RUNNING and 0 < self._remaining_seconds <= 10
        )

        # Completion
        if self._remaining_seconds <= 0 and self._state == RUNNING:
            self._complete()

    def _update_display(self):
        mins = self._remaining_seconds // 60
        secs = self._remaining_seconds % 60
        self._ring.set_countdown_text(f"{mins:02d}:{secs:02d}")

    # ── Completion sequence ─────────────────────────────────────────────
    def _complete(self):
        self._state = COMPLETED
        self._tick_timer.stop()
        self._kitty.set_running(False)
        self._start_btn.setText("Start")
        self._status_label.setText("Done! Your egg is ready! 🎉")

        # 1. Kitty jump
        self._kitty.trigger_jump()

        # 2. Ring shake
        self._ring.trigger_shake()
        self._ring.set_warning(False)

        # 3. Background glow expansion
        self._bg_glow.pulse()

        # 4. Particles
        self._particles.emit_continuous(
            cx=self.width() / 2,
            cy=self.height() * 0.4,
        )

        # 5. Sounds
        self._sound.play_bell()
        QTimer.singleShot(350, self._sound.play_meow)

    # ── Window dragging ─────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # ── Custom card painting ────────────────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        path = QPainterPath()
        path.addRoundedRect(
            0, 0, self.width(), self.height(),
            CORNER_RADIUS, CORNER_RADIUS,
        )

        # Subtle shadow beneath
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor(0, 0, 0, 40)))
        shadow_path = QPainterPath()
        shadow_path.addRoundedRect(
            2, 4, self.width() - 4, self.height() - 4,
            CORNER_RADIUS, CORNER_RADIUS,
        )
        p.drawPath(shadow_path)

        # Main gradient background
        grad = QLinearGradient(0, 0, 0, self.height())
        grad.setColorAt(0.0, QColor("#2C2C2E"))
        grad.setColorAt(1.0, QColor("#1C1C1E"))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor(255, 255, 255, 12), 1))
        p.drawPath(path)

        p.end()


# ═══════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Kitty Egg Timer")

    # Global font fallback
    font = QFont("SF Pro Display")
    if not font.exactMatch():
        font = QFont("Helvetica Neue")
    if not font.exactMatch():
        font = QFont("Arial")
    font.setPointSize(13)
    app.setFont(font)

    window = KittyTimerApp()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
