"""
Kitty Egg Timer — Animated Kitty Widget
========================================
QPainter-drawn cat face with blinking, ear wiggle, idle float,
tail sway, and jump animations.
"""

import math
import random

from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve,
    pyqtProperty, QRectF, QPointF,
)
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QLinearGradient
from PyQt6.QtWidgets import QWidget

from utils.theme import ACCENT_PINK, SOFT_BLUE, TEXT_PRIMARY, CARD_SURFACE


class KittyWidget(QWidget):
    """A cute QPainter-drawn cat with idle, running, and completion animations."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(180, 180)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # ── Internal state ──────────────────────────────────────────────
        self._blink_progress = 0.0      # 0 = open, 1 = closed
        self._ear_angle = 0.0           # degrees of ear wiggle
        self._float_offset = 0.0        # vertical idle bounce (px)
        self._tail_angle = 0.0          # tail sway degrees
        self._jump_offset = 0.0         # upward jump (px)
        self._is_running = False
        self._is_hovered = False

        # ── Blink timer ─────────────────────────────────────────────────
        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._start_blink)
        self._blink_timer.start(random.randint(2500, 5000))

        self._blink_anim_close = QPropertyAnimation(self, b"blink_progress", self)
        self._blink_anim_close.setDuration(100)
        self._blink_anim_close.setStartValue(0.0)
        self._blink_anim_close.setEndValue(1.0)
        self._blink_anim_close.finished.connect(self._blink_open)

        self._blink_anim_open = QPropertyAnimation(self, b"blink_progress", self)
        self._blink_anim_open.setDuration(100)
        self._blink_anim_open.setStartValue(1.0)
        self._blink_anim_open.setEndValue(0.0)

        # ── Ear wiggle animation ────────────────────────────────────────
        self._ear_anim = QPropertyAnimation(self, b"ear_angle", self)
        self._ear_anim.setDuration(400)
        self._ear_anim.setKeyValueAt(0.0, 0.0)
        self._ear_anim.setKeyValueAt(0.25, 8.0)
        self._ear_anim.setKeyValueAt(0.5, -6.0)
        self._ear_anim.setKeyValueAt(0.75, 4.0)
        self._ear_anim.setKeyValueAt(1.0, 0.0)
        self._ear_anim.setEasingCurve(QEasingCurve.Type.InOutSine)

        # ── Idle float (sine driven by QTimer) ──────────────────────────
        self._float_phase = 0.0
        self._float_timer = QTimer(self)
        self._float_timer.timeout.connect(self._update_float)
        self._float_timer.start(30)

        # ── Tail sway (sine driven by float timer when running) ─────────
        self._tail_phase = 0.0

        # ── Jump animation ──────────────────────────────────────────────
        self._jump_anim = QPropertyAnimation(self, b"jump_offset", self)
        self._jump_anim.setDuration(600)
        self._jump_anim.setKeyValueAt(0.0, 0.0)
        self._jump_anim.setKeyValueAt(0.35, -30.0)
        self._jump_anim.setKeyValueAt(0.5, -35.0)
        self._jump_anim.setKeyValueAt(0.75, -10.0)
        self._jump_anim.setKeyValueAt(1.0, 0.0)
        self._jump_anim.setEasingCurve(QEasingCurve.Type.OutBounce)

    # ── Qt Properties ───────────────────────────────────────────────────
    @pyqtProperty(float)
    def blink_progress(self):
        return self._blink_progress

    @blink_progress.setter
    def blink_progress(self, v):
        self._blink_progress = v
        self.update()

    @pyqtProperty(float)
    def ear_angle(self):
        return self._ear_angle

    @ear_angle.setter
    def ear_angle(self, v):
        self._ear_angle = v
        self.update()

    @pyqtProperty(float)
    def float_offset(self):
        return self._float_offset

    @float_offset.setter
    def float_offset(self, v):
        self._float_offset = v
        self.update()

    @pyqtProperty(float)
    def tail_angle(self):
        return self._tail_angle

    @tail_angle.setter
    def tail_angle(self, v):
        self._tail_angle = v
        self.update()

    @pyqtProperty(float)
    def jump_offset(self):
        return self._jump_offset

    @jump_offset.setter
    def jump_offset(self, v):
        self._jump_offset = v
        self.update()

    # ── Slot methods ────────────────────────────────────────────────────
    def _start_blink(self):
        self._blink_timer.setInterval(random.randint(2500, 5000))
        self._blink_anim_close.start()

    def _blink_open(self):
        self._blink_anim_open.start()

    def _update_float(self):
        self._float_phase += 0.06
        self._float_offset = math.sin(self._float_phase) * 5.0

        if self._is_running:
            self._tail_phase += 0.12
            self._tail_angle = math.sin(self._tail_phase) * 18.0
        else:
            # Gentle return to 0
            self._tail_angle *= 0.9

        self.update()

    # ── Public API ──────────────────────────────────────────────────────
    def set_running(self, running: bool):
        self._is_running = running

    def trigger_jump(self):
        self._jump_anim.start()

    # ── Hover events ────────────────────────────────────────────────────
    def enterEvent(self, event):
        self._is_hovered = True
        self._ear_anim.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hovered = False
        super().leaveEvent(event)

    # ── Painting ────────────────────────────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        cx = self.width() / 2
        cy = self.height() / 2 + self._float_offset + self._jump_offset

        self._draw_tail(p, cx, cy)
        self._draw_body(p, cx, cy)
        self._draw_ears(p, cx, cy)
        self._draw_face(p, cx, cy)

        p.end()

    def _draw_body(self, p: QPainter, cx: float, cy: float):
        """Draw the round cat head/body."""
        radius = 52
        grad = QLinearGradient(cx, cy - radius, cx, cy + radius)
        grad.setColorAt(0.0, QColor("#4A4A4E"))
        grad.setColorAt(1.0, QColor("#3A3A3C"))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor("#5A5A5E"), 1.5))
        p.drawEllipse(QPointF(cx, cy), radius, radius)

    def _draw_ears(self, p: QPainter, cx: float, cy: float):
        """Draw two triangular ears with inner pink."""
        p.save()
        p.translate(cx, cy)
        p.rotate(self._ear_angle)

        for side in (-1, 1):
            # Outer ear
            ear = QPainterPath()
            ear.moveTo(side * 20, -45)
            ear.lineTo(side * 45, -80)
            ear.lineTo(side * 50, -40)
            ear.closeSubpath()
            p.setBrush(QBrush(QColor("#4A4A4E")))
            p.setPen(QPen(QColor("#5A5A5E"), 1.5))
            p.drawPath(ear)

            # Inner ear (pink)
            inner = QPainterPath()
            inner.moveTo(side * 25, -48)
            inner.lineTo(side * 43, -73)
            inner.lineTo(side * 46, -44)
            inner.closeSubpath()
            p.setBrush(QBrush(ACCENT_PINK))
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPath(inner)

        p.restore()

    def _draw_face(self, p: QPainter, cx: float, cy: float):
        """Draw eyes, nose, mouth, whiskers."""
        # ── Eyes ────────────────────────────────────────────────────────
        eye_y = cy - 8
        for side in (-1, 1):
            ex = cx + side * 18
            if self._blink_progress > 0.8:
                # Closed — draw line
                p.setPen(QPen(TEXT_PRIMARY, 2.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawLine(QPointF(ex - 7, eye_y), QPointF(ex + 7, eye_y))
            else:
                # Open eye
                eye_h = 11 * (1.0 - self._blink_progress)
                p.setBrush(QBrush(TEXT_PRIMARY))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawEllipse(QPointF(ex, eye_y), 7, eye_h)
                # Pupil
                p.setBrush(QBrush(QColor("#1C1C1E")))
                p.drawEllipse(QPointF(ex, eye_y + 1), 3.5, min(5, eye_h * 0.6))
                # Highlight
                p.setBrush(QBrush(TEXT_PRIMARY))
                p.drawEllipse(QPointF(ex + 2, eye_y - 2), 1.8, 1.8)

        # ── Nose ────────────────────────────────────────────────────────
        nose_y = cy + 6
        nose = QPainterPath()
        nose.moveTo(cx, nose_y - 3)
        nose.lineTo(cx - 4, nose_y + 3)
        nose.lineTo(cx + 4, nose_y + 3)
        nose.closeSubpath()
        p.setBrush(QBrush(ACCENT_PINK))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawPath(nose)

        # ── Mouth ───────────────────────────────────────────────────────
        p.setPen(QPen(TEXT_PRIMARY, 1.5, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        mouth_y = nose_y + 5
        path = QPainterPath()
        path.moveTo(cx - 10, mouth_y)
        path.quadTo(cx - 5, mouth_y + 6, cx, mouth_y)
        path.quadTo(cx + 5, mouth_y + 6, cx + 10, mouth_y)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)

        # ── Whiskers ────────────────────────────────────────────────────
        p.setPen(QPen(QColor("#8E8E93"), 1.0))
        for side in (-1, 1):
            bx = cx + side * 22
            p.drawLine(QPointF(bx, cy + 2), QPointF(bx + side * 28, cy - 5))
            p.drawLine(QPointF(bx, cy + 5), QPointF(bx + side * 30, cy + 5))
            p.drawLine(QPointF(bx, cy + 8), QPointF(bx + side * 28, cy + 14))

    def _draw_tail(self, p: QPainter, cx: float, cy: float):
        """Draw a curving tail behind the body."""
        p.save()
        p.translate(cx + 40, cy + 30)
        p.rotate(self._tail_angle)

        tail = QPainterPath()
        tail.moveTo(0, 0)
        tail.cubicTo(15, -20, 30, -40, 20, -60)
        tail.cubicTo(15, -50, 5, -30, 0, 0)
        tail.closeSubpath()

        p.setBrush(QBrush(QColor("#4A4A4E")))
        p.setPen(QPen(QColor("#5A5A5E"), 1.5))
        p.drawPath(tail)
        p.restore()
