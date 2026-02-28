"""
Kitty Egg Timer — Animation Helpers
====================================
Factory functions for common QPropertyAnimations.
"""

from PyQt6.QtCore import (
    QEasingCurve, QPropertyAnimation, QObject, QPoint, QPointF,
    QSequentialAnimationGroup, QParallelAnimationGroup, QAbstractAnimation,
)
from PyQt6.QtWidgets import QGraphicsOpacityEffect, QWidget


def fade_in(widget: QWidget, duration: int = 500,
            start: float = 0.0, end: float = 1.0) -> QPropertyAnimation:
    """Attach an opacity effect and return a fade-in animation."""
    effect = QGraphicsOpacityEffect(widget)
    widget.setGraphicsEffect(effect)
    anim = QPropertyAnimation(effect, b"opacity", widget)
    anim.setDuration(duration)
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
    return anim


def fade_out(widget: QWidget, duration: int = 400) -> QPropertyAnimation:
    """Return a fade-out animation (opacity → 0)."""
    return fade_in(widget, duration, start=1.0, end=0.0)


def bounce_y(target: QObject, prop: bytes, base: float,
             amplitude: float = 12.0, duration: int = 600) -> QPropertyAnimation:
    """Vertical bounce: move up then back to base."""
    anim = QPropertyAnimation(target, prop)
    anim.setDuration(duration)
    anim.setKeyValueAt(0.0, base)
    anim.setKeyValueAt(0.4, base - amplitude)
    anim.setKeyValueAt(0.7, base + amplitude * 0.3)
    anim.setKeyValueAt(1.0, base)
    anim.setEasingCurve(QEasingCurve.Type.OutBounce)
    return anim


def scale_press(target: QObject, prop: bytes,
                normal: float = 1.0, pressed: float = 0.93,
                duration: int = 120) -> QPropertyAnimation:
    """Quick shrink for press feedback."""
    anim = QPropertyAnimation(target, prop)
    anim.setDuration(duration)
    anim.setStartValue(normal)
    anim.setEndValue(pressed)
    anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
    return anim


def shake(target: QObject, prop: bytes = b"pos",
          amplitude: int = 6, duration: int = 400) -> QSequentialAnimationGroup:
    """Horizontal shake animation (4 oscillations)."""
    group = QSequentialAnimationGroup(target)
    base = target.property(prop.decode()) or QPoint(0, 0)
    if isinstance(base, QPointF):
        base = base.toPoint()

    for i in range(4):
        direction = 1 if i % 2 == 0 else -1
        a = QPropertyAnimation(target, prop)
        a.setDuration(duration // 4)
        a.setStartValue(base)
        a.setEndValue(QPoint(base.x() + amplitude * direction, base.y()))
        a.setEasingCurve(QEasingCurve.Type.InOutSine)
        group.addAnimation(a)

    # Return to base
    ret = QPropertyAnimation(target, prop)
    ret.setDuration(duration // 8)
    ret.setStartValue(QPoint(base.x() + amplitude, base.y()))
    ret.setEndValue(base)
    group.addAnimation(ret)
    return group


def smooth_value(target: QObject, prop: bytes,
                 start: float, end: float,
                 duration: int = 300) -> QPropertyAnimation:
    """Generic smooth value interpolation."""
    anim = QPropertyAnimation(target, prop)
    anim.setDuration(duration)
    anim.setStartValue(start)
    anim.setEndValue(end)
    anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
    return anim
