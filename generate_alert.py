"""
Generate a simple alert sound for testing
This script creates a beep sound if you don't have an alert.wav file
"""
import numpy as np
from scipy.io import wavfile
import os


def generate_alert_sound(filename="data/alert.wav", duration=2.0, frequency=800):
    """
    Generate a simple alert beep sound
    
    Args:
        filename: Output filename
        duration: Duration in seconds
        frequency: Frequency of the beep in Hz
    """
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Sample rate
    sample_rate = 44100
    
    # Generate time array
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Generate beep with fade in/out to avoid clicks
    beep = np.sin(2 * np.pi * frequency * t)
    
    # Add amplitude modulation for more alerting sound
    modulation = np.sin(2 * np.pi * 4 * t)  # 4 Hz modulation
    beep = beep * (0.7 + 0.3 * modulation)
    
    # Apply fade in/out
    fade_samples = int(0.01 * sample_rate)  # 10ms fade
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)
    
    beep[:fade_samples] *= fade_in
    beep[-fade_samples:] *= fade_out
    
    # Normalize to 16-bit range
    beep = np.int16(beep * 32767 * 0.8)
    
    # Save as WAV file
    wavfile.write(filename, sample_rate, beep)
    
    print(f"Alert sound generated: {filename}")
    print(f"Duration: {duration}s, Frequency: {frequency}Hz")


if __name__ == "__main__":
    generate_alert_sound()
    print("\nNote: You need scipy to run this script.")
    print("Install with: pip install scipy")
    print("\nAlternatively, you can download any alert.wav file")
    print("and place it in the data/ directory.")
