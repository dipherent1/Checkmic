# ui.py (Final Version for Volume Control)

import tkinter as tk
from tkinter import font

class Application(tk.Tk):
    WINDOW_TITLE = "Audio Quality Assistant"
    WINDOW_SIZE = "350x150"
    COLORS = {
        "GOOD": "#4CAF50",
        "TOO QUIET": "#FFC107",
        "TOO LOUD": "#F44336",
        "CHECK PROFILE": "#2196F3",
        "DEFAULT": "#212121",
        "ERROR": "#F44336"
    }
    FONT_COLOR = "white"

    def __init__(self):
        super().__init__()
        self.title(self.WINDOW_TITLE)
        self.geometry(self.WINDOW_SIZE)
        self.configure(bg=self.COLORS["DEFAULT"])
        self.attributes('-topmost', True)
        
        # --- FINISHING TOUCH: Make the window a fixed size ---
        self.resizable(False, False)

        self.status_font = font.Font(family="Helvetica", size=24, weight="bold")
        self.rms_font = font.Font(family="Helvetica", size=12)
        self.status_label = tk.Label(self, text="INITIALIZING...", font=self.status_font, fg=self.FONT_COLOR, bg=self.COLORS["DEFAULT"], wraplength=330)
        self.status_label.pack(pady=(20, 10), padx=10, expand=True, fill='both')
        self.rms_label = tk.Label(self, text="RMS: --", font=self.rms_font, fg=self.FONT_COLOR, bg=self.COLORS["DEFAULT"])
        self.rms_label.pack(pady=(0, 20))

    def update_status(self, status, rms, update_full_status=True):
        def _update():
            self.rms_label.config(text=f"RMS: {rms:.3f}")
            if update_full_status:
                color = self.COLORS.get(status, self.COLORS["DEFAULT"])
                self.status_label.config(text=status, bg=color)
                self.configure(bg=color)
                self.rms_label.config(bg=color)
        self.after(0, _update)