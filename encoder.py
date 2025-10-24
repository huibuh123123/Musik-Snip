"""
MP3 encoding functionality for audio data.
"""

import os
import logging
import numpy as np
import lameenc
from typing import Optional

from config import MP3_QUALITY, SAMPLE_RATE, CHANNELS


logger = logging.getLogger(__name__)


class MP3EncoderError(Exception):
    """Custom exception for MP3 encoding errors."""
    pass


class MP3Encoder:
    """
    Handles MP3 encoding of audio data.

    Attributes:
        bitrate: MP3 bitrate in kbps
        quality: LAME encoder quality (0=best, 9=worst)
    """

    def __init__(self, bitrate: int = 192, quality: int = MP3_QUALITY):
        """
        Initialize the MP3 encoder.

        Args:
            bitrate: MP3 bitrate in kbps (default: 192)
            quality: Encoder quality 0-9, 0 is best (default: from config)
        """
        self.bitrate = bitrate
        self.quality = quality
        logger.info(f"MP3Encoder initialized with bitrate={bitrate}, quality={quality}")

    def encode(self, audio_data: np.ndarray, output_file: str) -> bool:
        """
        Encode audio data to MP3 format.

        Args:
            audio_data: NumPy array with audio data (float32, range -1.0 to 1.0)
            output_file: Path to output MP3 file

        Returns:
            True if encoding was successful, False otherwise

        Raises:
            MP3EncoderError: If encoding fails
        """
        try:
            logger.info(f"Starting MP3 encoding to {output_file}")

            # Create encoder
            encoder = lameenc.Encoder()
            encoder.set_bit_rate(self.bitrate)
            encoder.set_in_sample_rate(SAMPLE_RATE)
            encoder.set_channels(CHANNELS)
            encoder.set_quality(self.quality)

            # Convert float32 audio to int16 PCM
            pcm_data = (audio_data * 32767).astype(np.int16).tobytes()

            # Encode to MP3
            mp3_data = encoder.encode(pcm_data)
            mp3_data += encoder.flush()

            # Write to file
            with open(output_file, "wb") as f:
                f.write(mp3_data)

            file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
            logger.info(f"MP3 encoding successful. File size: {file_size_mb:.2f} MB")
            return True

        except Exception as e:
            logger.error(f"MP3 encoding failed: {e}")
            raise MP3EncoderError(f"Failed to encode MP3: {e}")

    def convert_wav_to_mp3(self, wav_file: str, mp3_file: str,
                           delete_wav: bool = True) -> bool:
        """
        Convert a WAV file to MP3.

        Args:
            wav_file: Path to input WAV file
            mp3_file: Path to output MP3 file
            delete_wav: Whether to delete WAV file after conversion

        Returns:
            True if conversion was successful

        Raises:
            MP3EncoderError: If conversion fails
        """
        try:
            import soundfile as sf

            # Read WAV file
            audio_data, sample_rate = sf.read(wav_file, dtype='float32')

            if sample_rate != SAMPLE_RATE:
                logger.warning(f"Sample rate mismatch: {sample_rate} != {SAMPLE_RATE}")

            # Encode to MP3
            success = self.encode(audio_data, mp3_file)

            # Delete WAV file if requested and encoding was successful
            if success and delete_wav and os.path.exists(wav_file):
                try:
                    os.remove(wav_file)
                    logger.info(f"Deleted temporary WAV file: {wav_file}")
                except Exception as e:
                    logger.warning(f"Failed to delete WAV file: {e}")

            return success

        except Exception as e:
            logger.error(f"WAV to MP3 conversion failed: {e}")
            raise MP3EncoderError(f"Failed to convert WAV to MP3: {e}")
