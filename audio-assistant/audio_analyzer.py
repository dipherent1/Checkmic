# audio_analyzer.py (DEBUGGING VERSION - BARE MINIMUM)

import sounddevice as sd
import numpy as np
import threading
import queue
import time

class AudioAnalyzer:
    # --- Configuration ---
    # Use a partial, simple name. 'AirPods' is better than 'AirPods Pro-78'
    # as it's more likely to match. Set to None to test default.
    DEVICE_NAME = "bluetooth"  # Use a partial name for more robust matching
    
    CHANNELS = 1
    
    # Let's use a dynamic sample rate but have a fallback
    SAMPLE_RATE = 48000 
    
    # We will use integer RMS for this test
    QUIET_THRESHOLD = 50
    LOUD_THRESHOLD = 8000

    def __init__(self, status_callback):
        self.status_callback = status_callback
        self.device_index = None
        
        # --- MORE ROBUST DEVICE FINDING ---
        try:
            self.device_index = self._find_device_index()
            device_info = sd.query_devices(self.device_index)
            self.sample_rate = int(device_info['default_samplerate'])
            print(f"Successfully configured device '{device_info['name']}' with sample rate {self.sample_rate}Hz.")
        except Exception as e:
            print(f"ERROR: Could not configure specified device. {e}")
            print("--- Falling back to default device ---")
            self.device_index = None # Use default
            device_info = sd.query_devices(self.device_index)
            self.sample_rate = int(device_info['default_samplerate'])
            print(f"Configured default device '{device_info['name']}' with sample rate {self.sample_rate}Hz.")

        self.audio_queue = queue.Queue()
        self.running = False
        self._worker_thread = threading.Thread(target=self._analysis_worker)
        self._worker_thread.daemon = True

    def _find_device_index(self):
        """Finds the device index that matches the device name."""
        print(f"Searching for device containing '{self.DEVICE_NAME}'...")
        if self.DEVICE_NAME is None:
            print("DEVICE_NAME is None, using default device.")
            return None
            
        devices = sd.query_devices()
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0 and self.DEVICE_NAME.lower() in device['name'].lower():
                print(f"SUCCESS: Found device '{device['name']}' at index {i}")
                return i
        raise RuntimeError(f"Could not find any input device with name containing '{self.DEVICE_NAME}'")

    def _audio_callback(self, indata, frames, time, status):
        """HIGH-PRIORITY: NO I/O, NO PRINT, NO HEAVY LOGIC."""
        # The ONLY job is to put a copy of the data onto the queue.
        self.audio_queue.put(indata.copy())

    def _analysis_worker(self):
        """LOW-PRIORITY: Pulls from queue and does simple analysis."""
        while self.running:
            try:
                # Get audio data from the queue
                float_data = self.audio_queue.get(timeout=1).flatten()
                
                # --- Let's convert back to int16 for simpler thresholds for now ---
                int_data = (float_data * 32767).astype(np.int16)
                rms = np.sqrt(np.mean(int_data.astype(np.float64)**2))

                # --- BARE MINIMUM ANALYSIS ---
                status = ""
                if rms < self.QUIET_THRESHOLD:
                    status = "TOO QUIET"
                elif rms > self.LOUD_THRESHOLD:
                    status = "TOO LOUD"
                else:
                    status = "GOOD"
                
                self.status_callback(status, rms)

            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in worker thread: {e}")
                self.status_callback("ERROR", 0)
                time.sleep(1)

    def start(self):
        if not self.running:
            self.running = True
            self._worker_thread.start()
            self.stream = sd.InputStream(
                device=self.device_index,
                channels=self.CHANNELS,
                samplerate=self.sample_rate,
                callback=self._audio_callback
            )
            self.stream.start()
            print("Stream started.")

    def stop(self):
        # ... (stop method is the same)
        if self.running:
            self.running = False
            self._worker_thread.join(timeout=1)
            if self.stream:
                self.stream.stop()
                self.stream.close()
            print("Stream stopped.")