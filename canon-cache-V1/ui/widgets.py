"""
CanonCache — Reusable UI Widget Components
"""

import tkinter as tk
from tkinter import ttk
from ui.theme import *


class StatusDot(tk.Canvas):
    """Animated pulsing status indicator dot."""

    def __init__(self, parent, size=10, **kwargs):
        super().__init__(parent, width=size, height=size,
                         bg=BG_SURFACE, highlightthickness=0, **kwargs)
        self._size = size
        self._color = TEXT_DISABLED
        self._oval = self.create_oval(1, 1, size-1, size-1, fill=self._color, outline="")
        self._pulse = False
        self._alpha = 1.0
        self._direction = -1

    def set_color(self, color: str, pulse: bool = False):
        self._color = color
        self._pulse = pulse
        self.itemconfig(self._oval, fill=color)
        if pulse:
            self._animate()

    def _animate(self):
        if not self._pulse:
            return
        # Simple blink by alternating fill
        current = self.itemcget(self._oval, "fill")
        self.itemconfig(self._oval, fill=self._color if current == BG_SURFACE else BG_SURFACE)
        self.after(600, self._animate)


class Card(tk.Frame):
    """Rounded-looking card frame."""

    def __init__(self, parent, **kwargs):
        bg = kwargs.pop("bg", BG_RAISED)
        super().__init__(parent, bg=bg,
                         highlightbackground=BG_BORDER, highlightthickness=1,
                         **kwargs)


class SectionLabel(tk.Label):
    """Bold section header label."""

    def __init__(self, parent, text, **kwargs):
        super().__init__(parent, text=text,
                         font=FONT_BOLD, fg=TEXT_PRIMARY, bg=BG_SURFACE,
                         **kwargs)


class MetricCard(tk.Frame):
    """A metric display card with label + value."""

    def __init__(self, parent, label: str, value: str = "—",
                 value_color: str = TEXT_PRIMARY, bg=BG_RAISED, **kwargs):
        super().__init__(parent, bg=bg,
                         highlightbackground=BG_BORDER, highlightthickness=1,
                         padx=PAD, pady=PAD_SM, **kwargs)
        self._bg = bg
        self._lbl = tk.Label(self, text=label.upper(),
                             font=FONT_SANS_SM, fg=TEXT_SECONDARY, bg=bg)
        self._lbl.pack(anchor="w")
        self._val = tk.Label(self, text=value,
                             font=("Segoe UI", 18, "bold"), fg=value_color, bg=bg)
        self._val.pack(anchor="w")

    def update(self, value: str, color: str = TEXT_PRIMARY):
        self._val.config(text=value, fg=color)


class StyledButton(tk.Button):
    """Styled flat button."""

    def __init__(self, parent, text, command=None, style="primary", **kwargs):
        colors = {
            "primary":  (ACCENT_BLUE,  BG_SURFACE),
            "success":  (ACCENT_GREEN, BG_SURFACE),
            "danger":   (ACCENT_RED,   BG_SURFACE),
            "secondary":(TEXT_SECONDARY, BG_RAISED),
            "ghost":    (TEXT_PRIMARY,  BG_SURFACE),
        }
        fg, abg = colors.get(style, colors["primary"])
        super().__init__(
            parent,
            text=text,
            command=command,
            font=FONT_BOLD,
            fg=fg,
            bg=abg,
            activeforeground=TEXT_PRIMARY,
            activebackground=BG_HOVER,
            relief="flat",
            cursor="hand2",
            padx=PAD,
            pady=6,
            bd=0,
            **kwargs,
        )
        self.bind("<Enter>", lambda e: self.config(bg=BG_HOVER))
        self.bind("<Leave>", lambda e: self.config(bg=abg))


class ProgressBar(tk.Frame):
    """Custom styled progress bar."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_RAISED,
                         highlightbackground=BG_BORDER, highlightthickness=1,
                         height=8, **kwargs)
        self._fill = tk.Frame(self, bg=ACCENT_BLUE, height=8)
        self._fill.place(x=0, y=0, relheight=1, width=0)
        self._pct = 0.0

    def set(self, fraction: float):
        """Set progress 0.0 – 1.0."""
        self._pct = max(0.0, min(1.0, fraction))
        self.update_idletasks()
        w = self.winfo_width()
        self._fill.place(width=int(w * self._pct))
        # Color changes
        if self._pct >= 1.0:
            self._fill.config(bg=ACCENT_GREEN)
        elif self._pct > 0.0:
            self._fill.config(bg=ACCENT_BLUE)

    def reset(self):
        self._fill.config(bg=ACCENT_BLUE)
        self.set(0.0)


class Separator(tk.Frame):
    """Thin horizontal divider."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BG_BORDER, height=1, **kwargs)


class ScrolledText(tk.Frame):
    """Text widget with scrollbar, styled for dark theme."""

    def __init__(self, parent, **kwargs):
        font = kwargs.pop("font", FONT_MONO_SM)
        fg = kwargs.pop("fg", TEXT_PRIMARY)
        bg = kwargs.pop("bg", BG_DEEP)
        height = kwargs.pop("height", 20)
        super().__init__(parent, bg=bg, **kwargs)
        self.text = tk.Text(
            self, font=font, fg=fg, bg=bg,
            insertbackground=ACCENT_BLUE,
            selectbackground=ACCENT_BLUE,
            selectforeground=TEXT_PRIMARY,
            relief="flat", bd=0,
            height=height,
            wrap=tk.WORD,
            state=tk.DISABLED,
        )
        sb = tk.Scrollbar(self, command=self.text.yview,
                          bg=BG_RAISED, troughcolor=BG_DEEP,
                          activebackground=BG_HOVER, relief="flat", width=10)
        self.text.config(yscrollcommand=sb.set)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        apply_tags(self.text)

    def append(self, text: str, tag: str = ""):
        self.text.config(state=tk.NORMAL)
        if tag:
            self.text.insert(tk.END, text, tag)
        else:
            self.text.insert(tk.END, text)
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)

    def clear(self):
        self.text.config(state=tk.NORMAL)
        self.text.delete("1.0", tk.END)
        self.text.config(state=tk.DISABLED)

    def set_text(self, text: str):
        self.clear()
        self.append(text)
