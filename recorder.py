"""
Audio recording functionality using PyAudioWPatch for WASAPI Loopback.
"""

import os
import logging
import datetime
import numpy as np
import soundfile as sf
from typing import Optional, Callable, List
from threading import Event
import time

try:
    import pyaudiowpatch as pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    import pyaudio
    PYAUDIO_AVAILABLE = False
    logging.warning("PyAudioWPatch not available, loopback recording may not work")

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
    Handles audio recording from system audio device using WASAPI Loopback.

    Attributes:
        sample_rate: Audio sample rate in Hz
        channels: Number of audio channels (1=mono, 2=stereo)
        device: Audio device info dict or device index
    """

    def __init__(self, sample_rate: int = SAMPLE_RATE, channels: int = CHANNELS,
                 device: Optional[dict] = None):
        """
        Initialize the audio recorder.

        Args:
            sample_rate: Sample rate in Hz (default: from config)
            channels: Number of channels (default: from config)
            device: Device info dict with 'index', 'name', 'is_loopback', etc.
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.device = device
        self.is_recording = False
        self.is_paused = False
        self.frames: List[bytes] = []
        self.stop_event = Event()
        self.pause_event = Event()
        self.pyaudio_instance = None
        self.stream = None
        self.current_level = 0.0

        logger.info(f"AudioRecorder initialized: rate={sample_rate}, channels={channels}, device={device}")

    @staticmethod
    def get_audio_devices() -> List[dict]:
        """
        Get list of available audio devices including WASAPI loopback devices.

        Returns:
            List of device info dictionaries with keys:
            - id: device index
            - name: device name
            - channels: max channels
            - sample_rate: default sample rate
            - is_loopback: True if this is a loopback device
            - is_default: True if this is the default loopback device
        """
        devices = []

        try:
            p = pyaudio.PyAudio()

            # Get default loopback device
            try:
                if PYAUDIO_AVAILABLE:
                    default_loopback = p.get_default_wasapi_loopback()
                    default_loopback_index = default_loopback['index'] if default_loopback else None
                else:
                    default_loopback_index = None
            except (OSError, AttributeError):
                default_loopback_index = None
                logger.warning("Could not get default WASAPI loopback device")

            # Enumerate all devices
            for i in range(p.get_device_count()):
                try:
                    device_info = p.get_device_info_by_index(i)

                    # Check if this is a loopback device
                    is_loopback = device_info.get('isLoopbackDevice', False)
                    max_channels = device_info.get('maxInputChannels', 0)

                    # Include loopback devices or regular input devices
                    if is_loopback or max_channels > 0:
                        devices.append({
                            'id': i,
                            'name': device_info['name'],
                            'channels': max_channels,
                            'sample_rate': device_info['defaultSampleRate'],
                            'is_loopback': is_loopback,
                            'is_default': (i == default_loopback_index),
                            'hostapi': device_info.get('hostApi', -1)
                        })

                except Exception as e:
                    logger.debug(f"Skipping device {i}: {e}")
                    continue

            p.terminate()

            # Sort: loopback devices first, then default loopback, then by name
            devices.sort(key=lambda d: (not d['is_loopback'], not d.get('is_default', False), d['name']))

            logger.info(f"Found {len(devices)} audio devices ({sum(1 for d in devices if d['is_loopback'])} loopback)")
            return devices

        except Exception as e:
            logger.error(f"Failed to query audio devices: {e}")
            return []

    def start_recording(self, duration: Optional[float] = None,
                       callback: Optional[Callable[[float], None]] = None) -> None:
        """
        Start audio recording. This method BLOCKS until recording is finished.

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
            self.current_level = 0.0

            # Get device info
            device_index = None
            device_channels = self.channels
            device_sample_rate = self.sample_rate

            if self.device:
                device_index = self.device.get('id')
                device_channels = self.device.get('channels', self.channels)
                device_sample_rate = int(self.device.get('sample_rate', self.sample_rate))
                logger.info(f"Using device {device_index}: {self.device.get('name')}")
            else:
                # Use default loopback device
                logger.info("Using default loopback device")

            # Update recorder settings based on device
            self.sample_rate = device_sample_rate
            # Use stereo if device supports it, otherwise use device's max channels
            if device_channels >= 2:
                self.channels = 2
            else:
                self.channels = device_channels

            logger.info(f"Starting recording (duration={duration}s, rate={self.sample_rate}, channels={self.channels})")

            # Initialize PyAudio
            self.pyaudio_instance = pyaudio.PyAudio()

            # Determine audio format
            if AUDIO_DTYPE == 'float32':
                audio_format = pyaudio.paFloat32
            elif AUDIO_DTYPE == 'int16':
                audio_format = pyaudio.paInt16
            else:
                audio_format = pyaudio.paFloat32

            # Open stream
            self.stream = self.pyaudio_instance.open(
                format=audio_format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=BUFFER_SIZE
            )

            logger.info("Audio stream opened successfully")

            # Recording loop (BLOCKING)
            start_time = time.time()

            try:
                while not self.stop_event.is_set():
                    # Check duration limit
                    elapsed = time.time() - start_time
                    if duration and elapsed >= duration:
                        logger.info(f"Duration limit reached: {elapsed:.1f}s")
                        break

                    # Call progress callback
                    if callback:
                        callback(elapsed)

                    # Read audio data
                    try:
                        if not self.is_paused and self.stream.is_active():
                            data = self.stream.read(BUFFER_SIZE, exception_on_overflow=False)
                            self.frames.append(data)

                            # Calculate audio level for visualization
                            try:
                                audio_array = np.frombuffer(data, dtype=np.float32 if AUDIO_DTYPE == 'float32' else np.int16)
                                if len(audio_array) > 0:
                                    if AUDIO_DTYPE == 'int16':
                                        audio_array = audio_array.astype(np.float32) / 32768.0
                                    # Calculate RMS and scale up for better visibility
                                    rms = np.sqrt(np.mean(audio_array ** 2))
                                    # Scale by 3 for better visibility (loopback audio can be quiet)
                                    self.current_level = float(min(rms * 3.0, 1.0))
                            except Exception as e:
                                logger.debug(f"Level calculation error: {e}")
                        elif self.is_paused:
                            # When paused, still update but don't record
                            time.sleep(0.05)
                    except Exception as e:
                        if not self.stop_event.is_set():
                            logger.warning(f"Stream read error: {e}")

                    time.sleep(0.01)  # Small delay to prevent CPU spinning

                logger.info("Recording stopped")

            except Exception as e:
                logger.error(f"Recording loop error: {e}")
                raise AudioRecorderError(f"Recording failed: {e}")

            finally:
                # Cleanup stream
                if self.stream:
                    try:
                        self.stream.stop_stream()
                        self.stream.close()
                    except Exception as e:
                        logger.warning(f"Error closing stream: {e}")

                if self.pyaudio_instance:
                    try:
                        self.pyaudio_instance.terminate()
                    except Exception as e:
                        logger.warning(f"Error terminating PyAudio: {e}")

        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.is_recording = False
            if self.stream:
                try:
                    self.stream.close()
                except:
                    pass
            if self.pyaudio_instance:
                try:
                    self.pyaudio_instance.terminate()
                except:
                    pass
            raise AudioRecorderError(f"Failed to start recording: {e}")

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
            # Convert bytes to numpy array
            audio_bytes = b''.join(self.frames)

            if AUDIO_DTYPE == 'float32':
                audio_data = np.frombuffer(audio_bytes, dtype=np.float32)
            elif AUDIO_DTYPE == 'int16':
                audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
            else:
                audio_data = np.frombuffer(audio_bytes, dtype=np.float32)

            # Reshape to (samples, channels) if stereo
            if self.channels > 1:
                audio_data = audio_data.reshape(-1, self.channels)

            logger.info(f"Retrieved audio data: shape={audio_data.shape}, dtype={audio_data.dtype}")
            return audio_data

        except Exception as e:
            logger.error(f"Failed to get audio data: {e}")
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
        return float(np.clip(self.current_level, 0.0, 1.0))

    def clear_data(self) -> None:
        """Clear recorded audio data from memory."""
        self.frames.clear()
        self.current_level = 0.0
        logger.info("Audio data cleared")
