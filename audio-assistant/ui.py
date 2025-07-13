# ui.py (With Partial Update Capability)

import tkinter as tk
from tkinter import font

class Application(tk.Tk):
    # ... (COLORS and other configs are the same) ...
    COLORS = {
        "GOOD": "#4CAF50",
        "TOO QUIET": "#FFC107",
        "TOO LOUD": "#F44336",
        "CHECK PROFILE": "#2196F3",
        "DEFAULT": "#212121",
        "ERROR": "#F44336"
    }
    FONT_COLOR = "white"
    # ...

    def __init__(self):
        # ... (__init__ is the same as before) ...
        super().__init__()
        self.title("Audio Quality Assistant")
        self.geometry("350x150")
        self.configure(bg=self.COLORS["DEFAULT"])
        self.attributes('-topmost', True)
        self.status_font = font.Font(family="Helvetica", size=24, weight="bold")
        self.rms_font = font.Font(family="Helvetica", size=12)
        self.status_label = tk.Label(self, text="INITIALIZING...", font=self.status_font, fg=self.COLORS["DEFAULT"], bg=self.COLORS["DEFAULT"], wraplength=330)
        self.status_label.pack(pady=(20, 10), padx=10, expand=True, fill='both')
        self.rms_label = tk.Label(self, text="RMS: --", font=self.rms_font, fg=self.COLORS["DEFAULT"], bg=self.COLORS["DEFAULT"])
        self.rms_label.pack(pady=(0, 20))

    def update_status(self, status, rms, update_full_status=True):
        """
        Updates the UI.
        :param status: The new status string.
        :param rms: The current RMS value.
        :param update_full_status: If False, only update the RMS text.
        """
        def _update():
            # Always update the RMS value for real-time feedback
            self.rms_label.config(text=f"RMS: {rms:.3f}")
            
            if update_full_status:
                color = self.COLORS.get(status, self.COLORS["DEFAULT"])
                self.status_label.config(text=status, bg=color)
                # We need to update the color of all elements for a consistent look
                self.configure(bg=color)
                self.rms_label.config(bg=color)
        
        # Schedule the update with the UI thread
        self.after(0, _update)