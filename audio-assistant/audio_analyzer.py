# audio_analyzer.py (Final Version for Volume Control)
"""
Real-time audio analyzer focusing on consistent volume levels.
This module captures audio, analyzes its RMS volume, and provides
status updates with asymmetric timing for a natural user experience.
"""

import sounddevice as sd
import numpy as np
import threading
import queue
import time
from scipy.fft import fft, fftfreq
import math


class AudioAnalyzer:
    DEBUG_CLARITY = True


    # --- CORE CONFIGURATION ---
    DEVICE_NAME = "default"  # Partial name of the target microphone
    CHANNELS = 1
    CHUNK_SIZE = 1024  # Number of audio samples per chunk

    # --- THRESHOLDS (Normalized to -1.0 to 1.0 float audio) ---
    # The "Yellow Zone" is our new "GOOD"
    LOUD_DB_THRESHOLD = -9.0    # Above this is the "Red Zone" -> TOO LOUD
    QUIET_DB_THRESHOLD = -20.0  # Below this is the "Green Zone" -> TOO QUIET
    # The "sweet spot" between -25dB and -9dB is our "Yellow Zone" -> GOOD


    # --- NEW: CLARITY ANALYSIS CONFIG ---
    # We define our frequency bands in Hz
    FREQ_BANDS = {
        "low": (60, 250),      # Bass/body of the voice
        "mid": (250, 2000),    # Core speech intelligibility
        "high": (2000, 8000)   # Sibilance and crispness ("s", "t" sounds)
    }
    # Thresholds for the energy percentage in each band
    CLARITY_THRESHOLDS = {
        "muffled_high_percent": 0.04, # If high-freq energy is less than 4%, it's muffled
        "tinny_low_percent": 0.10     # If low-freq energy is less than 10%, it's tinny
    }

    # --- CONSISTENCY & TIMING (in seconds) ---
    # Asymmetric timers for a better user experience
    PERSISTENCE_ATTACK = 0.1  # Fast reaction for starting to speak or clipping
    PERSISTENCE_DECAY = 3   # Slow reaction to natural pauses (going from GOOD to QUIET)
    PERSISTENCE_NORMAL = 1.0  # Standard reaction time for other state changes

    # --- BLUETOOTH PROFILE CHECK ---
    SILENT_STREAM_THRESHOLD_DB = -60.0 # If audio is quieter than -60dB for too long
    SILENT_STREAM_DURATION_S = 3


    def __init__(self, status_callback):
        self.status_callback = status_callback
        self.device_index = self._find_device_index()
        device_info = sd.query_devices(self.device_index)
        self.sample_rate = int(device_info['default_samplerate'])
        print(f"Configured device '{device_info['name']}' (Index: {self.device_index}) with sample rate {self.sample_rate}Hz.")

        if self.DEBUG_CLARITY:
            self.debug_energy_samples = []

        self.audio_queue = queue.Queue()
        self.running = False
        self.silent_stream_start_time = None
        self._worker_thread = threading.Thread(target=self._analysis_worker)
        self._worker_thread.daemon = True

    def _find_device_index(self):
        # ... (This method is perfect, no changes needed) ...
        print(f"Searching for device containing '{self.DEVICE_NAME}'...")
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0 and self.DEVICE_NAME.lower() in device['name'].lower():
                print(f"SUCCESS: Found device '{device['name']}' at index {i}")
                return i
        print("WARNING: Could not find specified device. Falling back to default.")
        return None

    def _audio_callback(self, indata, frames, time, status):
        self.audio_queue.put(indata.copy())

    def _analysis_worker(self):
        self.silent_stream_start_time = time.time()
        current_ui_status = "INITIALIZING"
        potential_new_status = "INITIALIZING"
        potential_status_start_time = time.time()

        while self.running:
            try:
                float_data = self.audio_queue.get(timeout=1).flatten()
                
                # 1. Calculate RMS as before
                rms = np.sqrt(np.mean(float_data**2))

                # 2. Convert RMS to dBFS
                # Add a small epsilon to prevent log(0) errors
                epsilon = 1e-9
                db = 20 * math.log10(rms + epsilon)

                # Always update the dB value in the UI for real-time feedback
                self.status_callback(current_ui_status, db, update_full_status=False)
                
                # 3. Use dB for all logic now
                raw_chunk_status = ""
                if self.silent_stream_start_time is not None:
                    if db > self.SILENT_STREAM_THRESHOLD_DB:
                        self.silent_stream_start_time = None
                    elif time.time() - self.silent_stream_start_time > self.SILENT_STREAM_DURATION_S:
                        raw_chunk_status = "CHECK PROFILE"
                
                if raw_chunk_status == "":
                    if db < self.QUIET_DB_THRESHOLD:
                        raw_chunk_status = "TOO QUIET"
                    elif db > self.LOUD_DB_THRESHOLD:
                        raw_chunk_status = "TOO LOUD"
                    else:
                        raw_chunk_status = "GOOD"


                # --- NEW: CLARITY ANALYSIS BLOCK ---
                if raw_chunk_status == "GOOD":
                    N = len(float_data)
                    freqs = fftfreq(N, 1 / self.sample_rate)
                    yf = np.abs(fft(float_data))

                    energy = {}
                    for band, (low_freq, high_freq) in self.FREQ_BANDS.items():
                        band_indices = np.where((freqs >= low_freq) & (freqs <= high_freq))
                        energy[band] = np.sum(yf[band_indices])
                    
                    total_energy = sum(energy.values())
                    if total_energy > 0:
                        # --- NEW: DEBUG LOGIC ---
                        if self.DEBUG_CLARITY:
                            # Add the current chunk's energy to our sample list
                            self.debug_energy_samples.append(energy)
                            
                            # Calculate how many samples we need for ~2 seconds of audio
                            # (Sample Rate / Chunk Size) * Time
                            num_samples_needed = (self.sample_rate / self.CHUNK_SIZE) * 2 

                            # If we have enough samples, calculate and print the average
                            if len(self.debug_energy_samples) > num_samples_needed:
                                # Calculate the average energy for each band across all samples
                                avg_energy = {band: np.mean([s[band] for s in self.debug_energy_samples]) for band in self.FREQ_BANDS}
                                avg_total_energy = sum(avg_energy.values())
                                
                                # Calculate the final average percentages
                                low_percent = avg_energy["low"] / avg_total_energy
                                mid_percent = avg_energy["mid"] / avg_total_energy
                                high_percent = avg_energy["high"] / avg_total_energy

                                print(f'--- AVERAGED DATA ---\n'
                                      f'  Low:  {low_percent:.2%}\n'
                                      f'  Mid:  {mid_percent:.2%}\n'
                                      f'  High: {high_percent:.2%}\n'
                                      f'---------------------\n')
                                
                                # Clear the samples to start a new averaging window
                                self.debug_energy_samples.clear()

                        # --- NORMAL OPERATION LOGIC ---
                        else:
                            low_percent = energy["low"] / total_energy
                            high_percent = energy["high"] / total_energy
                            if high_percent < self.CLARITY_THRESHOLDS["muffled_high_percent"]:
                                raw_chunk_status = "MUFFLED"
                            elif low_percent < self.CLARITY_THRESHOLDS["tinny_low_percent"]:
                                raw_chunk_status = "TINNY"

                if raw_chunk_status != potential_new_status:
                    potential_new_status = raw_chunk_status
                    potential_status_start_time = time.time()
                
                persistence_needed = self.PERSISTENCE_NORMAL
                if (current_ui_status == "TOO QUIET" and potential_new_status == "GOOD") or \
                   (current_ui_status == "GOOD" and potential_new_status == "TOO LOUD"):
                    persistence_needed = self.PERSISTENCE_ATTACK
                elif current_ui_status == "GOOD" and potential_new_status == "TOO QUIET":
                    persistence_needed = self.PERSISTENCE_DECAY

                if time.time() - potential_status_start_time >= persistence_needed:
                    if potential_new_status != current_ui_status:
                        current_ui_status = potential_new_status
                        if current_ui_status == "CHECK PROFILE":
                            self.status_callback("Set AirPods to HSP/HFP Profile", db, update_full_status=True)
                        else:
                            self.status_callback(current_ui_status, db, update_full_status=True)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in worker thread: {e}")

    def start(self):
        if not self.running:
            self.running = True
            self._worker_thread.start()
            self.stream = sd.InputStream(
                device=self.device_index,
                channels=self.CHANNELS,
                samplerate=self.sample_rate,
                blocksize=self.CHUNK_SIZE, # Explicitly set for clarity
                callback=self._audio_callback
            )
            self.stream.start()
            print("Audio stream started.")

    def stop(self):
        if self.running:
            self.running = False
            self._worker_thread.join(timeout=1)
            if self.stream: self.stream.stop(); self.stream.close()
            print("Stream stopped.")