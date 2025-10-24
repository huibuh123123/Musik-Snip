"""
Configuration constants for the Audio Recorder application.
"""

# Audio Settings
SAMPLE_RATE = 48000  # 48 kHz (standard for many devices)
CHANNELS = 2  # Stereo
AUDIO_DTYPE = 'float32'
BUFFER_SIZE = 1024

# MP3 Encoding Settings
MP3_BITRATE_OPTIONS = {
    'Low': 128,
    'Medium': 192,
    'High': 256,
    'Very High': 320
}
DEFAULT_MP3_BITRATE = 192
MP3_QUALITY = 2  # 0 = best quality, 9 = worst quality

# File Settings
OUTPUT_FOLDER = "aufnahmen"
TEMP_FILE_PREFIX = "temp_"
OUTPUT_FILE_PREFIX = "aufnahme_"
TIMESTAMP_FORMAT = "%Y-%m-%d_%H-%M-%S"

# GUI Settings
WINDOW_TITLE = "🎙️ System Audio Recorder"
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 700
WINDOW_RESIZABLE = True
GUI_THEME = "darkly"  # ttkbootstrap theme: darkly, flatly, cosmo, solar, etc.

# UI Colors
COLOR_START_BUTTON = "#4CAF50"
COLOR_STOP_BUTTON = "#E53935"
COLOR_PAUSE_BUTTON = "#FF9800"
COLOR_RECORDING = "red"
COLOR_READY = "gray"
COLOR_SUCCESS = "green"
COLOR_ERROR = "red"
COLOR_WARNING = "orange"

# Default Values
DEFAULT_TIMER_MINUTES = 5
UPDATE_INTERVAL_MS = 100  # Update UI every 100ms
TIMER_DISPLAY_INTERVAL_MS = 1000  # Update timer display every second

# Memory Management
MAX_MEMORY_MB = 500  # Maximum memory usage before writing to disk
CHUNK_SIZE = 44100 * 2 * 2 * 60  # ~1 minute of audio data (sample_rate * channels * bytes_per_sample * seconds)
