"""
Quick test script to verify all imports and basic functionality.
"""

import sys

print("Testing imports...")

# Test config
try:
    import config
    print("[OK] config.py imported successfully")
    print(f"  - Sample rate: {config.SAMPLE_RATE}")
    print(f"  - Channels: {config.CHANNELS}")
except Exception as e:
    print(f"[FAIL] config.py import failed: {e}")
    sys.exit(1)

# Test encoder
try:
    from encoder import MP3Encoder, MP3EncoderError
    print("[OK] encoder.py imported successfully")
    encoder = MP3Encoder()
    print(f"  - Encoder created with bitrate: {encoder.bitrate}")
except Exception as e:
    print(f"[FAIL] encoder.py import failed: {e}")
    sys.exit(1)

# Test recorder
try:
    from recorder import AudioRecorder, AudioRecorderError
    print("[OK] recorder.py imported successfully")
    recorder = AudioRecorder()
    print(f"  - Recorder created with sample_rate: {recorder.sample_rate}")

    # Test device enumeration
    devices = AudioRecorder.get_audio_devices()
    print(f"  - Found {len(devices)} audio input devices")
except Exception as e:
    print(f"[FAIL] recorder.py import failed: {e}")
    sys.exit(1)

# Test GUI (without starting Tk mainloop)
try:
    from gui import AudioRecorderGUI
    print("[OK] gui.py imported successfully")
except Exception as e:
    print(f"[FAIL] gui.py import failed: {e}")
    sys.exit(1)

# Test main
try:
    import main
    print("[OK] main.py imported successfully")
except Exception as e:
    print(f"[FAIL] main.py import failed: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("All imports successful!")
print("="*50)
print("\nThe application should be ready to run.")
print("Start with: python main.py")
