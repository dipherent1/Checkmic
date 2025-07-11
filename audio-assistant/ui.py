# ui.py

import tkinter as tk
from tkinter import font

class Application(tk.Tk):
    WINDOW_TITLE = "Audio Quality Assistant"
    WINDOW_SIZE = "350x150"
    COLORS = {
        "GOOD": "#4CAF50",       # Green
        "TOO QUIET": "#FFC107",  # Amber
        "TOO LOUD": "#F44336",   # Red
        "NOISY": "#FF9800",      # Orange <--- NEW
        "DEFAULT": "#212121",    # Dark Grey
        "ERROR": "#F44336"       # Red
    }
    FONT_COLOR = "white"

    def __init__(self):
        super().__init__()
        self.title(self.WINDOW_TITLE)
        self.geometry(self.WINDOW_SIZE)
        self.configure(bg=self.COLORS["DEFAULT"])
        self.attributes('-topmost', True)
        self.status_font = font.Font(family="Helvetica", size=28, weight="bold")
        self.rms_font = font.Font(family="Helvetica", size=12)
        self.status_label = tk.Label(self, text="INITIALIZING...", font=self.status_font, fg=self.FONT_COLOR, bg=self.COLORS["DEFAULT"])
        self.status_label.pack(pady=(20, 10))
        self.rms_label = tk.Label(self, text="RMS: --", font=self.rms_font, fg=self.FONT_COLOR, bg=self.COLORS["DEFAULT"])
        self.rms_label.pack(pady=(0, 20))

    def update_status(self, status, rms):
        def _update():
            color = self.COLORS.get(status, self.COLORS["DEFAULT"])
            self.status_label.config(text=status, bg=color)
            self.rms_label.config(text=f"RMS: {rms:.0f}", bg=color)
            self.configure(bg=color)
        self.after(0, _update)