# test_analyzer.py
"""
Test harness for the AudioAnalyzer class.

This script loads audio files from a specified directory, runs them through
the analyzer, and prints a detailed report for each file. This allows for
rapid, reproducible tuning of the analysis thresholds without needing
real-time audio input.
"""

import os
import soundfile as sf
import numpy as np
import time

# We import the brain of our application directly
from audio_analyzer import AudioAnalyzer

# --- CONFIGURATION ---
AUDIO_FILES_DIRECTORY = "Data/audio/"

# This is a dummy callback function. The test script will inspect the results
# directly instead of relying on a UI update.
def dummy_callback(status, value, update_full_status=True):
    pass

def analyze_audio_file(filepath, analyzer_instance):
    """Loads an audio file and processes it through the analyzer."""
    print(f"\nAnalyzing file: {os.path.basename(filepath)}")
    print("-" * 40)
    
    try:
        # Load the audio file. It returns the data as a float32 NumPy array
        # and the sample rate.
        audio_data, sample_rate = sf.read(filepath, dtype='float32')
        
        # If the audio is stereo, convert it to mono by averaging the channels
        if audio_data.ndim > 1 and audio_data.shape[1] > 1:
            audio_data = np.mean(audio_data, axis=1)
            
        print(f"  Duration: {len(audio_data) / sample_rate:.2f}s | Sample Rate: {sample_rate}Hz")

        # Manually set the analyzer's sample rate to match the file's
        analyzer_instance.sample_rate = sample_rate

        # Simulate the real-time chunking process
        chunk_size = analyzer_instance.CHUNK_SIZE
        num_chunks = len(audio_data) // chunk_size
        
        # --- Data Collection ---
        all_rms = []
        all_energies = []
        
        for i in range(num_chunks):
            chunk = audio_data[i * chunk_size : (i + 1) * chunk_size]
            
            # Skip silent chunks for a more meaningful average
            rms = np.sqrt(np.mean(chunk**2))
            if rms < 0.001: # Corresponds to -60dB, effectively silent
                continue
            
            all_rms.append(rms)

            # Perform FFT and get frequency energy
            N = len(chunk)
            freqs = np.fft.fftfreq(N, 1 / sample_rate)
            yf = np.abs(np.fft.fft(chunk))

            energy = {}
            for band, (low_freq, high_freq) in analyzer_instance.FREQ_BANDS.items():
                band_indices = np.where((freqs >= low_freq) & (freqs <= high_freq))
                energy[band] = np.sum(yf[band_indices])
            
            all_energies.append(energy)

        # --- Reporting ---
        if not all_rms:
            print("  Result: File is completely silent.")
            return

        # Calculate average dB
        avg_rms = np.mean(all_rms)
        avg_db = 20 * np.log10(avg_rms)
        
        # Calculate average frequency distribution
        avg_energy = {band: np.mean([e[band] for e in all_energies]) for band in analyzer_instance.FREQ_BANDS}
        total_avg_energy = sum(avg_energy.values())
        
        low_percent = avg_energy["low"] / total_avg_energy
        high_percent = avg_energy["high"] / total_avg_energy

        # Determine the final status based on the averages
        final_status = ""
        if avg_db < analyzer_instance.QUIET_DB_THRESHOLD:
            final_status = "TOO QUIET"
        elif avg_db > analyzer_instance.LOUD_DB_THRESHOLD:
            final_status = "TOO LOUD"
        else:
            # Only check clarity if volume is good
            if high_percent < analyzer_instance.CLARITY_THRESHOLDS["muffled_high_percent"]:
                final_status = "MUFFLED"
            elif low_percent < analyzer_instance.CLARITY_THRESHOLDS["tinny_low_percent"]:
                final_status = "TINNY"
            else:
                final_status = "GOOD"

        print(f"  Average dB: {avg_db:.2f} dB")
        print(f"  Frequency Profile: Low {low_percent:.1%}, High {high_percent:.1%}")
        print(f"  Predicted Status: {final_status}")

    except Exception as e:
        print(f"  Error processing file: {e}")

if __name__ == "__main__":
    # Create an instance of our analyzer. It won't be started,
    # we're just using it as a container for our settings and logic.
    analyzer = AudioAnalyzer(dummy_callback)
    
    # Find all .wav files in the directory
    audio_files = [f for f in os.listdir(AUDIO_FILES_DIRECTORY) if f.lower().endswith('.wav')]
    
    if not audio_files:
        print(f"No .wav files found in '{AUDIO_FILES_DIRECTORY}'.")
    else:
        for filename in audio_files:
            filepath = os.path.join(AUDIO_FILES_DIRECTORY, filename)
            analyze_audio_file(filepath, analyzer)