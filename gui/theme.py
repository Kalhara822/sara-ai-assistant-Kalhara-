"""
Theme & Styling Definitions for CustomTkinter GUI (Iron Man / JARVIS HUD)
"""

from config import config

class Theme:
    """Color palette and visual constants for SARA HUD."""

    # Core Colors
    BG_DARK       = config.ui.COLOR_BG_DARK
    CARD_BG       = config.ui.COLOR_CARD_BG
    SURFACE       = "#1A2236"               # Slightly elevated above CARD_BG
    CYAN_ACCENT   = config.ui.COLOR_ACCENT_PRIMARY
    BLUE_ACCENT   = config.ui.COLOR_ACCENT_SECONDARY
    TEXT_MAIN     = config.ui.COLOR_TEXT_PRIMARY
    TEXT_MUTED    = config.ui.COLOR_TEXT_MUTED
    ALERT_WARN    = config.ui.COLOR_ALERT_WARN
    ALERT_DANGER  = config.ui.COLOR_ALERT_DANGER
    SUCCESS       = config.ui.COLOR_SUCCESS

    # Semantic Aliases (used by newer components)
    ACCENT_CYAN   = CYAN_ACCENT
    ACCENT_BLUE   = BLUE_ACCENT
    ACCENT_GREEN  = SUCCESS
    ACCENT_WARN   = ALERT_WARN
    TEXT_PRIMARY  = TEXT_MAIN
    FONT_PRIMARY  = config.ui.FONT_FAMILY_PRIMARY

    # CustomTkinter Color Tuples (Light Mode, Dark Mode)
    COLOR_BG_TUPLE   = (BG_DARK, BG_DARK)
    COLOR_CARD_TUPLE = (CARD_BG, CARD_BG)
    COLOR_CYAN_TUPLE = (CYAN_ACCENT, CYAN_ACCENT)

    # Fonts
    FONT_FAMILY = config.ui.FONT_FAMILY_PRIMARY
    FONT_MONO   = config.ui.FONT_FAMILY_MONO

    FONT_HEADER    = (FONT_FAMILY, 20, "bold")
    FONT_SUBHEADER = (FONT_FAMILY, 14, "bold")
    FONT_BODY      = (FONT_FAMILY, 12, "normal")
    FONT_SMALL     = (FONT_FAMILY, 10, "normal")
    FONT_STATUS    = (FONT_MONO,   11, "normal")

    # Layout Spacing
    PADDING_SMALL  = 5
    PADDING_MEDIUM = 10
    PADDING_LARGE  = 20
    CORNER_RADIUS  = 12
