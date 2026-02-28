"""
Kitty Egg Timer — Particle System
==================================
Floating hearts and sparkles emitted on timer completion.
"""

import math
import random

from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QFont
from PyQt6.QtWidgets import QWidget

from utils.theme import ACCENT_PINK, SOFT_BLUE, SUCCESS_MINT


class _Particle:
    __slots__ = ("x", "y", "vx", "vy", "opacity", "size", "kind",
                 "color", "rotation", "rot_speed", "life", "max_life")

    def __init__(self, x: float, y: float, kind: str = "heart"):
        self.x = x
        self.y = y
        self.vx = random.uniform(-1.5, 1.5)
        self.vy = random.uniform(-3.0, -1.0)
        self.opacity = 1.0
        self.size = random.uniform(8, 18)
        self.kind = kind  # "heart" or "sparkle"
        self.rotation = random.uniform(0, 360)
        self.rot_speed = random.uniform(-4, 4)
        self.max_life = random.uniform(60, 120)  # frames
        self.life = 0

        colors = [ACCENT_PINK, SOFT_BLUE, SUCCESS_MINT,
                  QColor("#FFD700"), QColor("#FF85C0")]
        self.color = random.choice(colors)


class ParticleSystem(QWidget):
    """Overlay widget that emits floating hearts and sparkles."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setFixedSize(420, 680)

        self._particles: list[_Particle] = []
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._emit_count = 0

    def emit_burst(self, cx: float = 210, cy: float = 280, count: int = 30):
        """Spawn a burst of particles centered at (cx, cy)."""
        for _ in range(count):
            kind = random.choice(["heart", "sparkle", "sparkle"])
            pt = _Particle(
                cx + random.uniform(-30, 30),
                cy + random.uniform(-20, 20),
                kind=kind,
            )
            self._particles.append(pt)

        if not self._timer.isActive():
            self._timer.start(16)  # ~60 fps

    def emit_continuous(self, cx: float = 210, cy: float = 280):
        """Start continuous particle emission."""
        self._emit_cx = cx
        self._emit_cy = cy
        self._emit_count = 80  # frames of continuous emission
        if not self._timer.isActive():
            self._timer.start(16)

    def stop(self):
        self._emit_count = 0

    def clear(self):
        self._particles.clear()
        self._emit_count = 0
        self._timer.stop()
        self.update()

    def _tick(self):
        # Continuous emission
        if self._emit_count > 0:
            self._emit_count -= 1
            cx = getattr(self, "_emit_cx", 210)
            cy = getattr(self, "_emit_cy", 280)
            for _ in range(2):
                kind = random.choice(["heart", "sparkle"])
                self._particles.append(_Particle(
                    cx + random.uniform(-40, 40),
                    cy + random.uniform(-30, 30),
                    kind=kind,
                ))

        # Update particles
        alive = []
        for pt in self._particles:
            pt.life += 1
            pt.x += pt.vx
            pt.y += pt.vy
            pt.vy -= 0.01  # slight upward drift deceleration
            pt.rotation += pt.rot_speed
            # Fade out in last third of life
            if pt.life > pt.max_life * 0.6:
                pt.opacity = max(0, 1.0 - (pt.life - pt.max_life * 0.6) / (pt.max_life * 0.4))
            if pt.life < pt.max_life and pt.opacity > 0.01:
                alive.append(pt)

        self._particles = alive

        if not self._particles and self._emit_count <= 0:
            self._timer.stop()

        self.update()

    def paintEvent(self, event):
        if not self._particles:
            return

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        for pt in self._particles:
            p.save()
            p.translate(pt.x, pt.y)
            p.rotate(pt.rotation)
            p.setOpacity(pt.opacity)

            col = QColor(pt.color)
            col.setAlphaF(pt.opacity)

            if pt.kind == "heart":
                self._draw_heart(p, pt.size, col)
            else:
                self._draw_sparkle(p, pt.size, col)

            p.restore()

        p.end()

    @staticmethod
    def _draw_heart(p: QPainter, size: float, color: QColor):
        """Draw a tiny heart shape."""
        s = size / 2
        path = QPainterPath()
        path.moveTo(0, s * 0.4)
        path.cubicTo(-s, -s * 0.3, -s * 0.5, -s, 0, -s * 0.5)
        path.cubicTo(s * 0.5, -s, s, -s * 0.3, 0, s * 0.4)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(color))
        p.drawPath(path)

    @staticmethod
    def _draw_sparkle(p: QPainter, size: float, color: QColor):
        """Draw a four-pointed sparkle/star."""
        s = size / 2
        path = QPainterPath()
        for i in range(4):
            angle = math.radians(i * 90)
            ox = math.cos(angle) * s
            oy = math.sin(angle) * s
            path.moveTo(0, 0)
            path.lineTo(ox, oy)

        p.setPen(QPen(color, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawPath(path)

        # Center dot
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(color))
        p.drawEllipse(QPointF(0, 0), 2, 2)
