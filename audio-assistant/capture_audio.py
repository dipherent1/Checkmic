import pyaudio
import numpy as np

# --- Configuration Constants ---
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

QUIET_THRESHOLD = 500   # Below this, we consider it "too quiet".
LOUD_THRESHOLD = 15000  # Above this, we consider it "too loud" (clipping).

p = pyaudio.PyAudio()
stream = None

try:
    print("Opening audio stream... Press Ctrl+C to stop.")

    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    while True:
        data = stream.read(CHUNK)
        numpy_data = np.frombuffer(data, dtype=np.int16)

        # --- NEW in Phase 2: RMS Calculation ---
        # We calculate the Root Mean Square of the audio chunk.
        # Note: We cast to float64 to prevent overflow when squaring.
        rms = np.sqrt(np.mean(numpy_data.astype(np.float64)**2))

        # --- NEW in Phase 2: Status Logic ---
        # We determine the status based on the RMS value.
        status = ""
        if rms < QUIET_THRESHOLD:
            # Using '\r' at the beginning of the print statement moves the
            # cursor to the start of the line, allowing us to overwrite it.
            # The 'end=""' prevents it from printing a newline.
            print(f'\rStatus: TOO QUIET  (RMS: {rms:.0f})      ', end="")
        elif rms > LOUD_THRESHOLD:
            print(f'\rStatus: TOO LOUD!  (RMS: {rms:.0f})      ', end="")
        else:
            print(f'\rStatus: GOOD       (RMS: {rms:.0f})      ', end="")

except KeyboardInterrupt:
    print("\nStopping stream...")
except Exception as e:
    print(f"An error occurred: {e}")
finally:
    if stream is not None:
        stream.stop_stream()
        stream.close()
    p.terminate()
    print("Stream closed. Program terminated.")