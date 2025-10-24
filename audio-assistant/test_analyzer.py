# test_analyzer_v2.py
"""
Test harness for the AudioAnalyzer class.

This script loads audio files (WAV, MP3, OGG) from a specified directory,
runs them through the analyzer, and prints a formatted summary table of the
results. This allows for rapid, reproducible tuning of the analysis thresholds.
"""

import os
import soundfile as sf
import numpy as np
import time
import math

# We import the brain of our application directly
# Make sure this file is in the same directory as audio_analyzer.py
from audio_analyzer import AudioAnalyzer

# --- CONFIGURATION ---
AUDIO_FILES_DIRECTORY = "Data/audio/"
SUPPORTED_EXTENSIONS = ('.wav', '.mp3', '.ogg')

def dummy_callback(status, value, update_full_status=True):
    """A dummy callback function for initializing the analyzer."""
    pass

def analyze_audio_file(filepath, analyzer_instance):
    """
    Loads an audio file, processes it, and returns a dictionary of results.
    This function no longer prints, it only returns data.
    """
    filename = os.path.basename(filepath)
    
    try:
        audio_data, sample_rate = sf.read(filepath, dtype='float32')
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=1) # Convert to mono
            
    except Exception as e:
        # Handle cases where the file is unreadable or unsupported
        return {
            "filename": filename,
            "status": "ERROR",
            "db": "N/A",
            "low_pct": "N/A",
            "high_pct": "N/A",
            "error": str(e)
        }

    analyzer_instance.sample_rate = sample_rate
    chunk_size = 1024 # Use a fixed chunk size for testing

    all_rms = []
    all_energies = []
    
    for i in range(len(audio_data) // chunk_size):
        chunk = audio_data[i * chunk_size : (i + 1) * chunk_size]
        rms = np.sqrt(np.mean(chunk**2))
        if rms < 1e-6: # Skip silent chunks
            continue
        all_rms.append(rms)

        # Perform FFT and get frequency energy
        N = len(chunk)
        freqs = np.fft.fftfreq(N, 1 / sample_rate)
        yf = np.abs(np.fft.fft(chunk))
        energy = {band: np.sum(yf[np.where((freqs >= l) & (freqs <= h))]) for band, (l, h) in analyzer_instance.FREQ_BANDS.items()}
        all_energies.append(energy)

    if not all_rms:
        return {"filename": filename, "status": "Silent", "db": "-inf", "low_pct": "0%", "high_pct": "0%"}

    # Calculate final metrics from the collected data
    avg_rms = np.mean(all_rms)
    avg_db = 20 * math.log10(avg_rms)
    avg_energy = {band: np.mean([e[band] for e in all_energies]) for band in analyzer_instance.FREQ_BANDS}
    total_avg_energy = sum(avg_energy.values())
    low_percent = avg_energy["low"] / total_avg_energy
    high_percent = avg_energy["high"] / total_avg_energy

    # Determine the final predicted status
    final_status = ""
    if avg_db < analyzer_instance.QUIET_DB_THRESHOLD:
        final_status = "TOO QUIET"
    elif avg_db > analyzer_instance.LOUD_DB_THRESHOLD:
        final_status = "TOO LOUD"
    else: # Only check clarity if volume is good
        if high_percent < analyzer_instance.CLARITY_THRESHOLDS["muffled_high_percent"]:
            final_status = "MUFFLED"
        elif low_percent < analyzer_instance.CLARITY_THRESHOLDS["tinny_low_percent"]:
            final_status = "TINNY"
        else:
            final_status = "GOOD"
            
    return {
        "filename": filename,
        "status": final_status,
        "db": f"{avg_db:.1f}",
        "low_pct": f"{low_percent:.1%}",
        "high_pct": f"{high_percent:.1%}"
    }

def print_results_table(results):
    """Prints a formatted Markdown table from the analysis results."""
    print("\n--- Audio Analysis Summary ---")
    
    # Print table header
    print(f"| {'Filename':<30} | {'Predicted Status':<18} | {'Avg dB':<8} | {'Low Freq %':<12} | {'High Freq %':<12} |")
    # Print separator
    print(f"|{'-'*32}|{'-'*20}|{'-'*10}|{'-'*14}|{'-'*14}|")
    
    # Print each result row
    for res in results:
        # Handle error case for cleaner printing
        if res.get("error"):
            print(f"| {res['filename']:<30} | {'ERROR READING FILE':<18} | {'N/A':<8} | {'N/A':<12} | {'N/A':<12} |")
            print(f"| {'└> Error: ' + res['error']:<79} |")
        else:
            print(f"| {res['filename']:<30} | {res['status']:<18} | {res['db']:>8} | {res['low_pct']:>12} | {res['high_pct']:>12} |")


if __name__ == "__main__":
    if not os.path.exists(AUDIO_FILES_DIRECTORY):
        print(f"Error: Directory not found at '{AUDIO_FILES_DIRECTORY}'")
        exit()
        
    analyzer = AudioAnalyzer(dummy_callback)
    
    audio_files = [f for f in os.listdir(AUDIO_FILES_DIRECTORY) if f.lower().endswith(SUPPORTED_EXTENSIONS)]
    
    if not audio_files:
        print(f"No supported audio files {SUPPORTED_EXTENSIONS} found in '{AUDIO_FILES_DIRECTORY}'.")
    else:
        results = []
        for filename in sorted(audio_files):
            filepath = os.path.join(AUDIO_FILES_DIRECTORY, filename)
            result = analyze_audio_file(filepath, analyzer)
            results.append(result)
        
        print_results_table(results)