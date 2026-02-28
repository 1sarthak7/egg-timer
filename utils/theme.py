"""
Kitty Egg Timer — Design System / Theme Constants
==================================================
Central colour palette, fonts, radii, shadow parameters.
macOS Sonoma dark + cute accent theme.
"""

from PyQt6.QtGui import QColor, QFont


# ── Colour Palette ──────────────────────────────────────────────────────
BG_COLOR           = QColor("#1C1C1E")
CARD_SURFACE       = QColor("#2C2C2E")
ACCENT_PINK        = QColor("#FF6FAE")
SOFT_BLUE          = QColor("#7FDBFF")
SUCCESS_MINT       = QColor("#32D74B")
DANGER_RED         = QColor("#FF453A")
TEXT_PRIMARY        = QColor("#FFFFFF")
TEXT_SECONDARY      = QColor("#A1A1A6")

# Convenience hex strings for stylesheets
BG_HEX             = "#1C1C1E"
CARD_HEX           = "#2C2C2E"
ACCENT_PINK_HEX    = "#FF6FAE"
SOFT_BLUE_HEX      = "#7FDBFF"
SUCCESS_MINT_HEX   = "#32D74B"
DANGER_RED_HEX     = "#FF453A"
TEXT_PRIMARY_HEX    = "#FFFFFF"
TEXT_SECONDARY_HEX  = "#A1A1A6"

# Extra tonal shades
CARD_HOVER         = QColor("#3A3A3C")
CARD_HOVER_HEX     = "#3A3A3C"
RING_GLOW          = QColor(255, 111, 174, 80)   # semi-transparent pink
RING_GRADIENT_START = QColor("#FF6FAE")
RING_GRADIENT_END   = QColor("#7FDBFF")

# ── Typography ──────────────────────────────────────────────────────────
FONT_FAMILY = "SF Pro Display"  # fallback handled per-platform

def heading_font(size: int = 28, bold: bool = True) -> QFont:
    f = QFont(FONT_FAMILY, size)
    f.setBold(bold)
    return f

def body_font(size: int = 14, bold: bool = False) -> QFont:
    f = QFont(FONT_FAMILY, size)
    f.setBold(bold)
    return f

def mono_font(size: int = 40) -> QFont:
    f = QFont("SF Mono", size)
    f.setBold(True)
    return f

# ── Layout Constants ────────────────────────────────────────────────────
CORNER_RADIUS      = 24
BUTTON_RADIUS      = 16
CARD_PADDING       = 28
WINDOW_WIDTH       = 420
WINDOW_HEIGHT      = 680

# ── Shadow Defaults ─────────────────────────────────────────────────────
SHADOW_BLUR        = 40
SHADOW_OFFSET_Y    = 8
SHADOW_COLOR       = QColor(0, 0, 0, 100)
