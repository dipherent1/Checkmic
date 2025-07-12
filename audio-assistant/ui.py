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
        "NOISY": "#FF9800",      # Orange
        "CHECK PROFILE": "#2196F3", # Blue for information
        "DEFAULT": "#212121",    # Dark Grey
        "ERROR": "#F44336"       # Red
    }
    FONT_COLOR = "white"

    def __init__(self):
        super().__init__()
        # ... (rest of __init__ is the same) ...
        self.title(self.WINDOW_TITLE)
        self.geometry(self.WINDOW_SIZE)
        self.configure(bg=self.COLORS["DEFAULT"])
        self.attributes('-topmost', True)
        self.status_font = font.Font(family="Helvetica", size=24, weight="bold") # Slightly smaller for longer text
        self.rms_font = font.Font(family="Helvetica", size=12)
        self.status_label = tk.Label(self, text="INITIALIZING...", font=self.status_font, fg=self.FONT_COLOR, bg=self.COLORS["DEFAULT"], wraplength=330) # Add wraplength
        self.status_label.pack(pady=(20, 10), padx=10, expand=True, fill='both')
        self.rms_label = tk.Label(self, text="RMS: --", font=self.rms_font, fg=self.FONT_COLOR, bg=self.COLORS["DEFAULT"])
        self.rms_label.pack(pady=(0, 20))

    def update_status(self, status, rms):
        # ... (this function remains exactly the same) ...
        def _update():
            color = self.COLORS.get(status, self.COLORS["DEFAULT"])
            self.status_label.config(text=status, bg=color)
            self.rms_label.config(text=f"RMS: {rms:.3f}", bg=color) # Show decimal for float RMS
            self.configure(bg=color)
        self.after(0, _update)