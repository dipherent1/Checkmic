# list_devices_detailed.py

import sounddevice as sd

print("=================================================================")
print("             Detailed Audio Device Information")
print("=================================================================")

try:
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        # We only care about devices that can be used as input
        if device['max_input_channels'] > 0:
            print(f"\n--- Device Index: {i} ---")
            print(f"  Name: {device['name']}")
            print(f"  Host API: {sd.query_hostapis(device['hostapi'])['name']}")
            print(f"  Max Input Channels: {device['max_input_channels']}")
            print(f"  Default Sample Rate: {device['default_samplerate']} Hz")
    
    print("\n=================================================================")
    print("Look for your AirPods in the list above and note their Index number.")

except Exception as e:
    print(f"An error occurred: {e}")