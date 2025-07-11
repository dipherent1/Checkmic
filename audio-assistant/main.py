# main.py

from ui import Application
from audio_analyzer import AudioAnalyzer

def main():
    # 1. Create the UI application instance
    app = Application()

    # 2. Create the audio analyzer instance
    #    We pass the UI's update_status method as the callback.
    #    This is how the analyzer communicates with the UI.
    analyzer = AudioAnalyzer(status_callback=app.update_status)

    # 3. Define what happens when the window is closed
    def on_closing():
        print("Closing application...")
        analyzer.stop()
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_closing)

    # 4. Start the audio analysis
    analyzer.start()

    # 5. Start the UI main loop
    #    This is a blocking call and will run until the window is closed.
    app.mainloop()

if __name__ == "__main__":
    main()