"""
Kitty Egg Timer — Animated Button
===================================
Premium QPushButton with hover scale, press shrink, drop shadow,
and gradient background.
"""

from PyQt6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, pyqtProperty, QPointF, QRectF,
)
from PyQt6.QtGui import QColor, QFont, QPainter, QBrush, QPen, QLinearGradient, QPainterPath, QRadialGradient
from PyQt6.QtWidgets import QPushButton

from utils.theme import (
    ACCENT_PINK_HEX, CARD_HEX, CARD_HOVER_HEX,
    TEXT_PRIMARY_HEX, TEXT_SECONDARY_HEX,
    BUTTON_RADIUS, ACCENT_PINK, CARD_SURFACE, CARD_HOVER,
    TEXT_PRIMARY,
)


class AnimatedButton(QPushButton):
    """A premium button with hover/press micro-animations and soft shadow."""

    def __init__(self, text: str = "", accent: QColor = None,
                 parent=None, icon_text: str = ""):
        super().__init__(text, parent)
        self._accent = accent or ACCENT_PINK
        self._icon_text = icon_text
        self._scale = 1.0
        self._bg_opacity = 0.0  # hover highlight opacity
        self._is_hovered = False
        self._is_pressed = False

        self.setFixedHeight(46)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFont(QFont("SF Pro Display", 13, QFont.Weight.DemiBold))

        # NOTE: We do NOT use QGraphicsDropShadowEffect here because it
        # conflicts with custom paintEvent when parent widgets also have
        # graphics effects. Instead the shadow is drawn manually.
        self._shadow_opacity = 0.15

        # ── Scale animation ─────────────────────────────────────────────
        self._scale_anim = QPropertyAnimation(self, b"btn_scale", self)
        self._scale_anim.setDuration(150)
        self._scale_anim.setEasingCurve(QEasingCurve.Type.OutBack)

        # ── Hover bg animation ──────────────────────────────────────────
        self._hover_anim = QPropertyAnimation(self, b"bg_opacity", self)
        self._hover_anim.setDuration(200)
        self._hover_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

        # Remove default button styling
        self.setStyleSheet("background: transparent; border: none; color: transparent;")

    # ── Qt properties ───────────────────────────────────────────────────
    @pyqtProperty(float)
    def btn_scale(self):
        return self._scale

    @btn_scale.setter
    def btn_scale(self, v):
        self._scale = v
        self.update()

    @pyqtProperty(float)
    def bg_opacity(self):
        return self._bg_opacity

    @bg_opacity.setter
    def bg_opacity(self, v):
        self._bg_opacity = v
        self.update()

    # ── Events ──────────────────────────────────────────────────────────
    def enterEvent(self, event):
        self._is_hovered = True
        self._scale_anim.stop()
        self._scale_anim.setStartValue(self._scale)
        self._scale_anim.setEndValue(1.05)
        self._scale_anim.start()

        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._bg_opacity)
        self._hover_anim.setEndValue(1.0)
        self._hover_anim.start()

        self._shadow_opacity = 0.25
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._is_hovered = False
        self._scale_anim.stop()
        self._scale_anim.setStartValue(self._scale)
        self._scale_anim.setEndValue(1.0)
        self._scale_anim.start()

        self._hover_anim.stop()
        self._hover_anim.setStartValue(self._bg_opacity)
        self._hover_anim.setEndValue(0.0)
        self._hover_anim.start()

        self._shadow_opacity = 0.15
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._is_pressed = True
        self._scale_anim.stop()
        self._scale_anim.setStartValue(self._scale)
        self._scale_anim.setEndValue(0.93)
        self._scale_anim.setDuration(100)
        self._scale_anim.start()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._is_pressed = False
        self._scale_anim.stop()
        self._scale_anim.setStartValue(self._scale)
        target = 1.05 if self._is_hovered else 1.0
        self._scale_anim.setEndValue(target)
        self._scale_anim.setDuration(150)
        self._scale_anim.start()
        super().mouseReleaseEvent(event)

    # ── Custom painting ─────────────────────────────────────────────────
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2

        p.translate(cx, cy)
        p.scale(self._scale, self._scale)
        p.translate(-cx, -cy)

        # ── Soft shadow (drawn manually instead of QGraphicsEffect) ───
        shadow_rect = QRectF(2, 4, w - 4, h - 2)
        shadow_grad = QRadialGradient(shadow_rect.center(), max(w, h) * 0.6)
        shadow_grad.setColorAt(0.0, QColor(0, 0, 0, int(self._shadow_opacity * 255)))
        shadow_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(shadow_grad))
        p.drawRoundedRect(shadow_rect, BUTTON_RADIUS, BUTTON_RADIUS)

        # ── Background ──────────────────────────────────────────────────
        bg_rect = QRectF(0, 0, w, h - 2)
        path = QPainterPath()
        path.addRoundedRect(bg_rect, BUTTON_RADIUS, BUTTON_RADIUS)

        # Base card color
        base_color = QColor(CARD_SURFACE)
        # Hovered → accent tinted
        if self._bg_opacity > 0.01:
            r = base_color.red() + int((self._accent.red() - base_color.red()) * self._bg_opacity * 0.35)
            g = base_color.green() + int((self._accent.green() - base_color.green()) * self._bg_opacity * 0.35)
            b = base_color.blue() + int((self._accent.blue() - base_color.blue()) * self._bg_opacity * 0.35)
            base_color = QColor(r, g, b)

        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0.0, base_color.lighter(115))
        grad.setColorAt(1.0, base_color)

        p.setPen(QPen(QColor(255, 255, 255, 15), 1))
        p.setBrush(QBrush(grad))
        p.drawPath(path)

        # ── Text ────────────────────────────────────────────────────────
        p.setPen(QPen(TEXT_PRIMARY))
        p.setFont(self.font())

        display = self._icon_text + "  " + self.text() if self._icon_text else self.text()
        p.drawText(bg_rect, Qt.AlignmentFlag.AlignCenter, display)

        p.end()
