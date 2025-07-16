# ui.py (With dB Markings on the Meter)

import tkinter as tk
from tkinter import font
import math

# Custom widget for the dB meter bar
class dBMeter(tk.Canvas):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.min_db = -60
        self.max_db = 0
        
        self.green_yellow_threshold = -20
        self.yellow_red_threshold = -9
        
        self.current_db = self.min_db

        # --- NEW: Define where to draw the numbers ---
        # We'll draw a tick mark every 5 dB.
        self.tick_marks = range(self.min_db, self.max_db + 1, 5)
        self.tick_font = font.Font(family="Helvetica", size=8)

        self.bind("<Configure>", self.draw_meter)

    def db_to_x(self, db):
        # ... (This function is the same) ...
        db_clamped = max(self.min_db, min(db, self.max_db))
        percent = (db_clamped - self.min_db) / (self.max_db - self.min_db)
        return percent * self.winfo_width()

    def draw_meter(self, event=None):
        self.delete("all")
        width = self.winfo_width()
        height = self.winfo_height()
        
        if width <= 1 or height <= 1:
            return
            
        # Define the height of the meter bar itself to leave space for text
        bar_height = height - 15

        # --- Draw the colored background bar ---
        # ... (This section is the same) ...
        green_width = self.db_to_x(self.green_yellow_threshold)
        yellow_width = self.db_to_x(self.yellow_red_threshold) - green_width
        red_width = width - (green_width + yellow_width)
        
        self.create_rectangle(0, 0, green_width, bar_height, fill="#4CAF50", outline="")
        self.create_rectangle(green_width, 0, green_width + yellow_width, bar_height, fill="#FFC107", outline="")
        self.create_rectangle(green_width + yellow_width, 0, width, bar_height, fill="#F44336", outline="")

        # --- NEW: Draw the tick marks and numbers ---
        for db_val in self.tick_marks:
            x = self.db_to_x(db_val)
            # Draw a small vertical line for the tick
            self.create_line(x, bar_height - 5, x, bar_height, fill="white")
            # Draw the text just below the tick
            self.create_text(x, bar_height + 7, text=str(db_val), fill="white", font=self.tick_font, anchor='center')

        # --- Draw the live indicator ---
        indicator_x = self.db_to_x(self.current_db)
        # Make the indicator a triangle like in the OBS image
        self.create_polygon(
            indicator_x - 4, bar_height - 5,
            indicator_x + 4, bar_height - 5,
            indicator_x, bar_height,
            fill="black", outline="white"
        )
        

    def update_db(self, db_value):
        self.current_db = db_value
        self.draw_meter()


# Main Application Window
class Application(tk.Tk):
    WINDOW_TITLE = "Audio Quality Assistant"
    WINDOW_SIZE = "350x180" # Increased height slightly for the numbers

    def __init__(self):
        super().__init__()
        self.title(self.WINDOW_TITLE)
        self.geometry(self.WINDOW_SIZE)
        self.configure(bg="#212121")
        self.attributes('-topmost', True)
        self.resizable(False, False)

        # Create the dB Meter widget. Increased its height as well.
        self.db_meter = dBMeter(self, bg="#212121", height=55, highlightthickness=0)
        self.db_meter.pack(pady=(15, 5), padx=20, fill='x')

        # Create the text labels for status and dB value
        status_font = font.Font(family="Helvetica", size=24, weight="bold")
        self.status_label = tk.Label(self, text="INITIALIZING...", font=status_font, fg="white", bg="#212121")
        self.status_label.pack(pady=5)
        
        db_font = font.Font(family="Helvetica", size=12)
        self.db_label = tk.Label(self, text="-60.0 dB", font=db_font, fg="white", bg="#212121")
        self.db_label.pack(pady=5)

    def update_status(self, status, db_value, update_full_status=True):
        # ... (This function is the same as the last version) ...
        def _update():
            self.db_meter.update_db(db_value)
            self.db_label.config(text=f"{db_value:.1f} dB")
            if update_full_status:
                self.status_label.config(text=status)
        self.after(0, _update)