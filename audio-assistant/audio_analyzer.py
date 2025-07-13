# audio_analyzer.py (With Asymmetric Timing)

import sounddevice as sd
import numpy as np
import threading
import queue
import time

class AudioAnalyzer:
    DEVICE_NAME = "default"
    CHANNELS = 1

    # --- UPDATED: Asymmetric Timing ---
    PERSISTENCE_NORMAL = 1.0  # For most transitions (e.g., GOOD -> LOUD)
    PERSISTENCE_ATTACK = 0.1  # Fast transition into speaking (QUIET -> GOOD)
    PERSISTENCE_DECAY = 3   # Slow transition for pauses (GOOD -> QUIET)

    QUIET_THRESHOLD = 0.01
    LOUD_THRESHOLD = 0.5
    SILENT_STREAM_THRESHOLD = 0.001
    SILENT_STREAM_DURATION_S = 3

    # ... (__init__ and other methods are the same) ...
    def __init__(self, status_callback):
        self.status_callback = status_callback
        self.sample_rate = 48000
        self.device_index = self._find_device_index()
        
        device_info = sd.query_devices(self.device_index)
        self.sample_rate = int(device_info['default_samplerate'])
        print(f"Configured device '{device_info['name']}' (Index: {self.device_index}) with sample rate {self.sample_rate}Hz.")

        self.audio_queue = queue.Queue()
        self.running = False
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
                rms = np.sqrt(np.mean(float_data**2))
                
                # --- NEW: Immediately update RMS value on UI ---
                # We call the callback on every frame, but only for the RMS value.
                self.status_callback(current_ui_status, rms, update_full_status=False)
                
                raw_chunk_status = ""

                if self.silent_stream_start_time is not None:
                    if rms > self.SILENT_STREAM_THRESHOLD:
                        self.silent_stream_start_time = None
                    elif time.time() - self.silent_stream_start_time > self.SILENT_STREAM_DURATION_S:
                        raw_chunk_status = "CHECK PROFILE"
                
                if raw_chunk_status == "":
                    if rms < self.QUIET_THRESHOLD:
                        raw_chunk_status = "TOO QUIET"
                    elif rms > self.LOUD_THRESHOLD:
                        raw_chunk_status = "TOO LOUD"
                    else:
                        raw_chunk_status = "GOOD"

                # Check if the raw status has changed
                if raw_chunk_status != potential_new_status:
                    potential_new_status = raw_chunk_status
                    potential_status_start_time = time.time()
                
                # --- NEW: Select the correct timer based on the transition ---
                persistence_needed = self.PERSISTENCE_NORMAL
                if current_ui_status == "TOO QUIET" and potential_new_status == "GOOD":
                    persistence_needed = self.PERSISTENCE_ATTACK
                elif current_ui_status == "GOOD" and potential_new_status == "TOO QUIET":
                    persistence_needed = self.PERSISTENCE_DECAY

                # Check if the potential state has persisted long enough
                if time.time() - potential_status_start_time >= persistence_needed:
                    if potential_new_status != current_ui_status:
                        current_ui_status = potential_new_status
                        # Now we do the full UI update
                        if current_ui_status == "CHECK PROFILE":
                            self.status_callback("Set AirPods to HSP/HFP Profile", rms, update_full_status=True)
                        else:
                            self.status_callback(current_ui_status, rms, update_full_status=True)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in worker thread: {e}")

    # ... (start and stop methods are the same) ...
    def start(self):
        if not self.running:
            self.running = True
            self._worker_thread.start()
            self.stream = sd.InputStream(device=self.device_index, channels=self.CHANNELS, samplerate=self.sample_rate, blocksize=1024,callback=self._audio_callback)
            self.stream.start()
            print("Stream started.")

    def stop(self):
        if self.running:
            self.running = False
            self._worker_thread.join(timeout=1)
            if self.stream: self.stream.stop(); self.stream.close()
            print("Stream stopped.")