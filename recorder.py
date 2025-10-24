"""
Audio recording functionality using sounddevice.
"""

import os
import logging
import datetime
import numpy as np
import sounddevice as sd
import soundfile as sf
from typing import Optional, Callable, List
from threading import Event

from config import (
    SAMPLE_RATE, CHANNELS, AUDIO_DTYPE, BUFFER_SIZE,
    OUTPUT_FOLDER, TEMP_FILE_PREFIX, OUTPUT_FILE_PREFIX, TIMESTAMP_FORMAT
)


logger = logging.getLogger(__name__)


class AudioRecorderError(Exception):
    """Custom exception for audio recording errors."""
    pass


class AudioRecorder:
    """
    Handles audio recording from system audio device.

    Attributes:
        sample_rate: Audio sample rate in Hz
        channels: Number of audio channels (1=mono, 2=stereo)
        device: Audio input device ID or name
    """

    def __init__(self, sample_rate: int = SAMPLE_RATE, channels: int = CHANNELS,
                 device: Optional[int] = None):
        """
        Initialize the audio recorder.

        Args:
            sample_rate: Sample rate in Hz (default: from config)
            channels: Number of channels (default: from config)
            device: Audio device ID (default: system default)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self.is_recording = False
        self.is_paused = False
        self.frames: List[np.ndarray] = []
        self.stop_event = Event()
        self.pause_event = Event()

        logger.info(f"AudioRecorder initialized: rate={sample_rate}, channels={channels}, device={device}")

    @staticmethod
    def get_audio_devices() -> List[dict]:
        """
        Get list of available audio input devices.

        Returns:
            List of device info dictionaries
        """
        try:
            devices = sd.query_devices()
            input_devices = []

            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    input_devices.append({
                        'id': i,
                        'name': device['name'],
                        'channels': device['max_input_channels'],
                        'sample_rate': device['default_samplerate']
                    })

            logger.info(f"Found {len(input_devices)} input devices")
            return input_devices

        except Exception as e:
            logger.error(f"Failed to query audio devices: {e}")
            return []

    def start_recording(self, duration: Optional[float] = None,
                       callback: Optional[Callable[[float], None]] = None) -> None:
        """
        Start audio recording.

        Args:
            duration: Recording duration in seconds (None = unlimited)
            callback: Optional callback function called with elapsed time

        Raises:
            AudioRecorderError: If recording cannot be started
        """
        if self.is_recording:
            logger.warning("Recording already in progress")
            return

        try:
            self.is_recording = True
            self.is_paused = False
            self.frames = []
            self.stop_event.clear()
            self.pause_event.clear()

            logger.info(f"Starting recording (duration={duration}s)")

            def audio_callback(indata, frames_count, time_info, status):
                """Callback for audio stream."""
                if status:
                    logger.warning(f"Audio callback status: {status}")

                if self.stop_event.is_set():
                    raise sd.CallbackStop

                if not self.is_paused:
                    self.frames.append(indata.copy())

            # Start audio stream
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=AUDIO_DTYPE,
                callback=audio_callback,
                device=self.device,
                blocksize=BUFFER_SIZE
            ):
                import time
                start_time = time.time()

                while not self.stop_event.is_set():
                    elapsed = time.time() - start_time

                    # Call progress callback
                    if callback:
                        callback(elapsed)

                    # Check duration limit
                    if duration and elapsed >= duration:
                        logger.info(f"Duration limit reached: {elapsed:.1f}s")
                        break

                    time.sleep(0.1)

            logger.info("Recording stopped")

        except Exception as e:
            logger.error(f"Recording failed: {e}")
            self.is_recording = False
            raise AudioRecorderError(f"Failed to record audio: {e}")

    def stop_recording(self) -> None:
        """Stop the current recording."""
        if not self.is_recording:
            logger.warning("No recording in progress")
            return

        logger.info("Stopping recording")
        self.stop_event.set()
        self.is_recording = False
        self.is_paused = False

    def pause_recording(self) -> None:
        """Pause the current recording."""
        if not self.is_recording:
            logger.warning("No recording in progress")
            return

        self.is_paused = True
        logger.info("Recording paused")

    def resume_recording(self) -> None:
        """Resume a paused recording."""
        if not self.is_recording:
            logger.warning("No recording in progress")
            return

        self.is_paused = False
        logger.info("Recording resumed")

    def get_audio_data(self) -> Optional[np.ndarray]:
        """
        Get the recorded audio data as numpy array.

        Returns:
            NumPy array with audio data, or None if no data
        """
        if not self.frames:
            logger.warning("No audio data recorded")
            return None

        try:
            audio_data = np.concatenate(self.frames, axis=0)
            logger.info(f"Retrieved audio data: shape={audio_data.shape}")
            return audio_data
        except Exception as e:
            logger.error(f"Failed to concatenate audio frames: {e}")
            return None

    def save_to_wav(self, filename: Optional[str] = None) -> str:
        """
        Save recorded audio to WAV file.

        Args:
            filename: Output filename (default: auto-generated with timestamp)

        Returns:
            Path to saved file

        Raises:
            AudioRecorderError: If saving fails
        """
        audio_data = self.get_audio_data()
        if audio_data is None:
            raise AudioRecorderError("No audio data to save")

        try:
            # Create output folder if needed
            if not os.path.exists(OUTPUT_FOLDER):
                os.makedirs(OUTPUT_FOLDER)
                logger.info(f"Created output folder: {OUTPUT_FOLDER}")

            # Generate filename if not provided
            if filename is None:
                timestamp = datetime.datetime.now().strftime(TIMESTAMP_FORMAT)
                filename = os.path.join(OUTPUT_FOLDER, f"{OUTPUT_FILE_PREFIX}{timestamp}.wav")

            # Save to WAV file
            sf.write(filename, audio_data, self.sample_rate)
            file_size_mb = os.path.getsize(filename) / (1024 * 1024)
            logger.info(f"Saved WAV file: {filename} ({file_size_mb:.2f} MB)")

            return filename

        except Exception as e:
            logger.error(f"Failed to save WAV file: {e}")
            raise AudioRecorderError(f"Failed to save audio: {e}")

    def get_audio_level(self) -> float:
        """
        Get current audio level (RMS) for visualization.

        Returns:
            Audio level as float (0.0 to 1.0)
        """
        if not self.frames or len(self.frames) == 0:
            return 0.0

        try:
            # Get last frame
            last_frame = self.frames[-1]
            # Calculate RMS
            rms = np.sqrt(np.mean(last_frame ** 2))
            return float(np.clip(rms, 0.0, 1.0))
        except Exception as e:
            logger.error(f"Failed to calculate audio level: {e}")
            return 0.0

    def clear_data(self) -> None:
        """Clear recorded audio data from memory."""
        self.frames.clear()
        logger.info("Audio data cleared")
