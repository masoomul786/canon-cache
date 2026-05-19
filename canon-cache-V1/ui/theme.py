"""
CanonCache — UI Theme Constants
Professional dark research theme.
"""

# ── Color Palette ─────────────────────────────────────────────────────────────
BG_DEEP      = "#0d1117"   # Deep background (GitHub-dark inspired)
BG_SURFACE   = "#161b22"   # Panel surfaces
BG_RAISED    = "#21262d"   # Slightly raised cards / inputs
BG_BORDER    = "#30363d"   # Subtle borders
BG_HOVER     = "#2d333b"   # Hover state

ACCENT_BLUE  = "#58a6ff"   # Primary accent (links, highlights)
ACCENT_GREEN = "#3fb950"   # Success / positive
ACCENT_AMBER = "#d29922"   # Warning / in-progress
ACCENT_RED   = "#f85149"   # Error / danger
ACCENT_PURPLE= "#bc8cff"   # Secondary accent (canonical prompts)
ACCENT_CYAN  = "#39d0d8"   # Info accents

TEXT_PRIMARY  = "#e6edf3"  # Main readable text
TEXT_SECONDARY= "#8b949e"  # Muted labels
TEXT_DISABLED = "#484f58"  # Disabled / placeholder

# ── Typography ────────────────────────────────────────────────────────────────
FONT_SANS  = ("Segoe UI", 10)
FONT_SANS_SM = ("Segoe UI", 9)
FONT_SANS_LG = ("Segoe UI", 12)
FONT_SANS_XL = ("Segoe UI", 14, "bold")
FONT_BOLD  = ("Segoe UI", 10, "bold")
FONT_MONO  = ("Consolas", 10)
FONT_MONO_SM = ("Consolas", 9)
FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_SUBTITLE = ("Segoe UI", 11)

# ── Spacing ───────────────────────────────────────────────────────────────────
PAD = 12
PAD_SM = 6
PAD_LG = 20

# ── Widget Dimensions ─────────────────────────────────────────────────────────
BTN_HEIGHT  = 32
INPUT_HEIGHT = 32
SIDEBAR_W   = 240
HEADER_H    = 56

# ── Status Colors ─────────────────────────────────────────────────────────────
STATUS_COLORS = {
    "connected":    ACCENT_GREEN,
    "connecting":   ACCENT_AMBER,
    "disconnected": ACCENT_RED,
    "running":      ACCENT_AMBER,
    "done":         ACCENT_GREEN,
    "error":        ACCENT_RED,
    "idle":         TEXT_SECONDARY,
}

# ── Tag configs for text widgets ──────────────────────────────────────────────
def apply_tags(text_widget):
    """Apply rich text tags to a tk.Text widget."""
    text_widget.tag_config("heading",      foreground=ACCENT_BLUE,   font=("Segoe UI", 11, "bold"))
    text_widget.tag_config("subheading",   foreground=ACCENT_PURPLE, font=("Segoe UI", 10, "bold"))
    text_widget.tag_config("value",        foreground=TEXT_PRIMARY,  font=("Consolas", 10))
    text_widget.tag_config("label",        foreground=TEXT_SECONDARY,font=("Segoe UI", 9))
    text_widget.tag_config("good",         foreground=ACCENT_GREEN)
    text_widget.tag_config("warn",         foreground=ACCENT_AMBER)
    text_widget.tag_config("bad",          foreground=ACCENT_RED)
    text_widget.tag_config("info",         foreground=ACCENT_CYAN)
    text_widget.tag_config("muted",        foreground=TEXT_SECONDARY)
    text_widget.tag_config("mono",         font=("Consolas", 9),     foreground=TEXT_PRIMARY)
    text_widget.tag_config("prompt_raw",   foreground="#ffa657")
    text_widget.tag_config("prompt_can",   foreground=ACCENT_PURPLE)
    text_widget.tag_config("divider",      foreground=BG_BORDER)
    text_widget.tag_config("user_msg",     foreground="#ffa657",     font=("Segoe UI", 10, "bold"))
    text_widget.tag_config("assistant_msg",foreground=ACCENT_BLUE,   font=("Segoe UI", 10, "bold"))
    text_widget.tag_config("system_msg",   foreground=TEXT_SECONDARY,font=("Segoe UI", 9, "italic"))
