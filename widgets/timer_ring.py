"""
Kitty Egg Timer — Circular Progress Ring
==========================================
Gradient arc ring with countdown text, glow pulse, and shake effect.
"""

import math

from PyQt6.QtCore import (
    Qt, QRectF, QPointF, QTimer,
    QPropertyAnimation, QEasingCurve,
    pyqtProperty, pyqtSignal, QPoint,
    QSequentialAnimationGroup,
)
from PyQt6.QtGui import (
    QPainter, QColor, QPen, QConicalGradient,
    QRadialGradient, QBrush, QFont,
)
from PyQt6.QtWidgets import QWidget, QGraphicsDropShadowEffect

from utils.theme import (
    ACCENT_PINK, SOFT_BLUE, TEXT_PRIMARY, TEXT_SECONDARY,
    RING_GRADIENT_START, RING_GRADIENT_END, RING_GLOW,
)


class TimerRing(QWidget):
    """Circular progress ring with gradient stroke and glow effects."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(280, 280)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # ── State ───────────────────────────────────────────────────────
        self._progress = 1.0           # 1.0 = full, 0.0 = done
        self._glow_opacity = 0.0       # pulsing glow
        self._countdown_text = ""
        self._ring_width = 8.0
        self._is_warning = False       # last 10 seconds

        # ── Glow pulse animation ────────────────────────────────────────
        self._glow_anim = QPropertyAnimation(self, b"glow_opacity", self)
        self._glow_anim.setDuration(800)
        self._glow_anim.setStartValue(0.2)
        self._glow_anim.setEndValue(0.9)
        self._glow_anim.setEasingCurve(QEasingCurve.Type.InOutSine)
        self._glow_anim.setLoopCount(-1)  # infinite

        # ── Shake animation ─────────────────────────────────────────────
        self._shake_group = None
        self._base_pos = None

    # ── Qt Properties ───────────────────────────────────────────────────
    @pyqtProperty(float)
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, v):
        self._progress = max(0.0, min(1.0, v))
        self.update()

    @pyqtProperty(float)
    def glow_opacity(self):
        return self._glow_opacity

    @glow_opacity.setter
    def glow_opacity(self, v):
        self._glow_opacity = v
        self.update()

    # ── Public API ──────────────────────────────────────────────────────
    def set_countdown_text(self, text: str):
        self._countdown_text = text
        self.update()

    def set_warning(self, on: bool):
        if on and not self._is_warning:
            self._is_warning = True
            self._glow_anim.start()
        elif not on and self._is_warning:
            self._is_warning = False
            self._glow_anim.stop()
            self._glow_opacity = 0.0
            self.update()

    def trigger_shake(self):
        """Shake the ring widget on completion."""
        if self._base_pos is None:
            self._base_pos = self.pos()

        base = self._base_pos
        group = QSequentialAnimationGroup(self)
        amp = 6
        for i in range(6):
            d = 1 if i % 2 == 0 else -1
            a = QPropertyAnimation(self, b"pos")
            a.setDuration(50)
            a.setStartValue(base)
            a.setEndValue(QPoint(base.x() + amp * d, base.y()))
            a.setEasingCurve(QEasingCurve.Type.InOutSine)
            group.addAnimation(a)
            amp = max(2, amp - 1)

        # Return to base
        ret = QPropertyAnimation(self, b"pos")
        ret.setDuration(50)
        ret.setEndValue(base)
        group.addAnimation(ret)

        self._shake_group = group
        group.start()

    def reset(self):
        self._progress = 1.0
        self._countdown_text = ""
        self._glow_opacity = 0.0
        self._is_warning = False
        self._glow_anim.stop()
        if self._base_pos is not None:
            self.move(self._base_pos)
        self.update()

    # ── Painting ────────────────────────────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        size = min(self.width(), self.height())
        margin = 20
        rect = QRectF(margin, margin, size - 2 * margin, size - 2 * margin)

        # ── Background track ────────────────────────────────────────────
        track_pen = QPen(QColor(60, 60, 64), self._ring_width,
                         Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        p.setPen(track_pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(rect)

        # ── Gradient arc ────────────────────────────────────────────────
        if self._progress > 0.001:
            center = rect.center()
            grad = QConicalGradient(center, 90)
            grad.setColorAt(0.0, RING_GRADIENT_START)
            grad.setColorAt(0.5, SOFT_BLUE)
            grad.setColorAt(1.0, RING_GRADIENT_END)

            arc_pen = QPen(QBrush(grad), self._ring_width + 2,
                           Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            p.setPen(arc_pen)
            # Qt drawArc: angles in 1/16th degree, start at 12 o'clock (90°)
            span = int(self._progress * 360 * 16)
            p.drawArc(rect, 90 * 16, -span)

        # ── Glow overlay ────────────────────────────────────────────────
        if self._glow_opacity > 0.01:
            center = rect.center()
            r = rect.width() / 2
            glow_grad = QRadialGradient(center, r + 20)

            if self._is_warning:
                glow_col = QColor(255, 69, 58, int(self._glow_opacity * 120))
            else:
                glow_col = QColor(255, 111, 174, int(self._glow_opacity * 100))
            glow_grad.setColorAt(0.7, glow_col)
            glow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(glow_grad))
            p.drawEllipse(rect.adjusted(-20, -20, 20, 20))

        # ── Countdown text ──────────────────────────────────────────────
        if self._countdown_text:
            font = QFont("SF Mono", 36)
            font.setBold(True)
            p.setFont(font)
            p.setPen(QPen(TEXT_PRIMARY))
            p.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._countdown_text)

        p.end()
