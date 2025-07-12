# audio_analyzer.py (Production-Ready Version)

import sounddevice as sd
import numpy as np
import threading
import queue
import time
import noisereduce as nr

class AudioAnalyzer:
    DEVICE_NAME = "default"  # We'll search for a device with this in its name
    CHANNELS = 1

    # Using float thresholds for data between -1.0 and 1.0
    QUIET_THRESHOLD = 0.01
    LOUD_THRESHOLD = 0.5
    NOISY_THRESHOLD_RATIO = 0.75
    
    # Time to build the noise profile
    NOISE_PROFILE_DURATION_S = 2
    
    # --- NEW: Logic for detecting silent stream (wrong BT profile) ---
    SILENT_STREAM_THRESHOLD = 0.001 # If RMS is below this for a while
    SILENT_STREAM_DURATION_S = 3 # If it's silent for this long after starting

    

    def __init__(self, status_callback):
        self.status_callback = status_callback
        self.sample_rate = 48000  # Default, will be updated
        self.device_index = self._find_device_index() # Automatically find the device
        
        device_info = sd.query_devices(self.device_index)
        self.sample_rate = int(device_info['default_samplerate'])
        print(f"Configured device '{device_info['name']}' (Index: {self.device_index}) with sample rate {self.sample_rate}Hz.")

        self.audio_queue = queue.Queue()
        self.running = False
        self.noise_profile = None
        self.noise_profile_samples = np.array([], dtype=np.float32)
        
        self.silent_stream_start_time = None
        
        self._worker_thread = threading.Thread(target=self._analysis_worker)
        self._worker_thread.daemon = True

    def _find_device_index(self):
        print(f"Searching for device containing '{self.DEVICE_NAME}'...")
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0 and self.DEVICE_NAME.lower() in device['name'].lower():
                print(f"SUCCESS: Found device '{device['name']}' at index {i}")
                return i
        print("WARNING: Could not find specified device. Falling back to default.")
        return None # Use default device

    def _audio_callback(self, indata, frames, time, status):
        self.audio_queue.put(indata.copy())

    def _analysis_worker(self):
        self.silent_stream_start_time = time.time()
        
        while self.running:
            try:
                float_data = self.audio_queue.get(timeout=1).flatten()
                rms = np.sqrt(np.mean(float_data**2))

                # --- NEW: Check for silent stream ---
                if self.silent_stream_start_time is not None:
                    if rms > self.SILENT_STREAM_THRESHOLD:
                        # We got sound! Disable the check.
                        self.silent_stream_start_time = None
                    elif time.time() - self.silent_stream_start_time > self.SILENT_STREAM_DURATION_S:
                        # It's been silent for too long, likely wrong BT profile
                        self.status_callback("CHECK PROFILE", rms)
                        continue

                # --- Full analysis logic ---
                if self.noise_profile is None:
                    noise_chunks_needed = int(self.NOISE_PROFILE_DURATION_S * self.sample_rate)
                    self.noise_profile_samples = np.append(self.noise_profile_samples, float_data)
                    if len(self.noise_profile_samples) >= noise_chunks_needed:
                        self.noise_profile = self.noise_profile_samples
                        print("Noise profile created.")
                    else:
                        self.status_callback("PROFILING", rms)
                    continue

                status = ""
                if rms < self.QUIET_THRESHOLD:
                    status = "TOO QUIET"
                else:
                    reduced_chunk = nr.reduce_noise(y=float_data, sr=self.sample_rate, y_noise=self.noise_profile)
                    rms_reduced = np.sqrt(np.mean(reduced_chunk**2))
                    reduction_ratio = (rms - rms_reduced) / rms if rms > 0 else 0

                    if reduction_ratio > self.NOISY_THRESHOLD_RATIO:
                        status = "NOISY"
                    elif rms > self.LOUD_THRESHOLD:
                        status = "TOO LOUD"
                    else:
                        status = "GOOD"
                
                self.status_callback(status, rms)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in worker thread: {e}")

    def start(self):
        if not self.running:
            self.running = True
            self._worker_thread.start()
            self.stream = sd.InputStream(device=self.device_index, channels=self.CHANNELS, samplerate=self.sample_rate, callback=self._audio_callback)
            self.stream.start()
            print("Stream started.")

    def stop(self):
        if self.running:
            self.running = False
            self._worker_thread.join(timeout=1)
            if self.stream: self.stream.stop(); self.stream.close()
            print("Stream stopped.")