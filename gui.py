"""
GUI for the Audio Recorder application with modern design using ttkbootstrap.
"""

import os
import logging
import datetime
from tkinter import messagebox, filedialog
from threading import Thread
from typing import Optional

import ttkbootstrap as ttk
from ttkbootstrap.constants import *

from config import (
    WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_RESIZABLE, GUI_THEME,
    DEFAULT_TIMER_MINUTES, TIMER_DISPLAY_INTERVAL_MS,
    MP3_BITRATE_OPTIONS, DEFAULT_MP3_BITRATE,
    OUTPUT_FOLDER, OUTPUT_FILE_PREFIX, TIMESTAMP_FORMAT
)
from recorder import AudioRecorder, AudioRecorderError
from encoder import MP3Encoder, MP3EncoderError


logger = logging.getLogger(__name__)


class AudioRecorderGUI:
    """
    Main GUI class for the Audio Recorder application with modern design.
    """

    def __init__(self, root: ttk.Window):
        """
        Initialize the GUI.

        Args:
            root: ttkbootstrap Window
        """
        self.root = root
        self.recorder = AudioRecorder()
        self.encoder: Optional[MP3Encoder] = None
        self.available_devices = []  # List of available audio devices

        # State variables
        self.is_recording = False
        self.is_paused = False
        self.start_time = 0.0
        self.elapsed_time = 0.0
        self.output_path = OUTPUT_FOLDER
        self.timer_end_time = None  # Calculated end time for timer
        self.timer_stop_scheduled = None  # ID for scheduled timer stop

        # Setup window
        self.setup_window()

        # Create GUI elements
        self.create_widgets()

        # Load audio devices
        self.load_audio_devices()

        logger.info("GUI initialized with modern theme")

    def setup_window(self) -> None:
        """Configure the main window."""
        self.root.title(WINDOW_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(WINDOW_RESIZABLE, WINDOW_RESIZABLE)

    def create_widgets(self) -> None:
        """Create all GUI widgets with modern design."""

        # Main container with padding
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=BOTH, expand=YES)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="System Audio Recorder",
            font=("Segoe UI", 16, "bold"),
            bootstyle="inverse-dark"
        )
        title_label.pack(pady=(0, 10))

        # Device selection frame
        device_frame = ttk.Labelframe(
            main_frame,
            text="🎧 Audio-Gerät",
            padding=8,
            bootstyle="primary"
        )
        device_frame.pack(fill=X, pady=(0, 8))

        self.device_var = ttk.StringVar()
        self.device_combo = ttk.Combobox(
            device_frame,
            textvariable=self.device_var,
            state="readonly",
            font=("Segoe UI", 10),
            bootstyle="primary"
        )
        self.device_combo.pack(fill=X)

        # Settings frame
        settings_frame = ttk.Labelframe(
            main_frame,
            text="⚙️ Einstellungen",
            padding=8,
            bootstyle="secondary"
        )
        settings_frame.pack(fill=X, pady=(0, 8))

        # Timer settings with minutes AND seconds
        timer_frame = ttk.Frame(settings_frame)
        timer_frame.pack(fill=X, pady=(0, 5))

        ttk.Label(
            timer_frame,
            text="⏱️ Timer:",
            font=("Segoe UI", 10, "bold")
        ).pack(side=LEFT, padx=(0, 10))

        # Minutes spinbox
        ttk.Label(timer_frame, text="Min:").pack(side=LEFT, padx=(0, 5))
        self.timer_minutes = ttk.Spinbox(
            timer_frame,
            from_=0,
            to=999,
            width=5,
            font=("Segoe UI", 10),
            bootstyle="secondary"
        )
        self.timer_minutes.set(DEFAULT_TIMER_MINUTES)
        self.timer_minutes.pack(side=LEFT, padx=(0, 15))

        # Seconds spinbox
        ttk.Label(timer_frame, text="Sek:").pack(side=LEFT, padx=(0, 5))
        self.timer_seconds = ttk.Spinbox(
            timer_frame,
            from_=0,
            to=59,
            width=5,
            font=("Segoe UI", 10),
            bootstyle="secondary"
        )
        self.timer_seconds.set(0)
        self.timer_seconds.pack(side=LEFT, padx=(0, 15))

        # Timer activate button (toggle style)
        self.timer_enabled = ttk.BooleanVar(value=False)
        self.timer_button = ttk.Checkbutton(
            timer_frame,
            text="Timer aktivieren",
            variable=self.timer_enabled,
            command=self.on_timer_toggle,
            bootstyle="success-round-toggle"
        )
        self.timer_button.pack(side=LEFT)

        # Timer end time display
        self.timer_end_label = ttk.Label(
            settings_frame,
            text="",
            font=("Segoe UI", 9),
            bootstyle="info"
        )
        self.timer_end_label.pack(fill=X, pady=(0, 5))

        # Quality settings with bitrate display
        quality_frame = ttk.Frame(settings_frame)
        quality_frame.pack(fill=X, pady=(0, 5))

        ttk.Label(
            quality_frame,
            text="🎵 MP3-Qualität:",
            font=("Segoe UI", 10, "bold")
        ).pack(side=LEFT, padx=(0, 10))

        # Create quality options with bitrate
        quality_options = [
            f"{name} ({bitrate} kbps)"
            for name, bitrate in MP3_BITRATE_OPTIONS.items()
        ]

        self.quality_var = ttk.StringVar(value=f"Medium ({DEFAULT_MP3_BITRATE} kbps)")
        quality_combo = ttk.Combobox(
            quality_frame,
            textvariable=self.quality_var,
            values=quality_options,
            state="readonly",
            width=20,
            font=("Segoe UI", 10),
            bootstyle="secondary"
        )
        quality_combo.pack(side=LEFT)

        # Output folder selection
        folder_frame = ttk.Frame(settings_frame)
        folder_frame.pack(fill=X)

        ttk.Label(
            folder_frame,
            text="📁 Speicherort:",
            font=("Segoe UI", 10, "bold")
        ).pack(side=LEFT, padx=(0, 10))

        self.folder_label = ttk.Label(
            folder_frame,
            text=OUTPUT_FOLDER,
            font=("Segoe UI", 9),
            bootstyle="primary"
        )
        self.folder_label.pack(side=LEFT, fill=X, expand=YES, padx=(0, 10))

        ttk.Button(
            folder_frame,
            text="Ändern",
            command=self.choose_output_folder,
            bootstyle="outline-secondary",
            width=10
        ).pack(side=RIGHT)

        # Status display with modern card design
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=X, pady=(0, 5))

        # Status card
        status_card = ttk.Frame(status_frame, bootstyle="dark")
        status_card.pack(fill=X, pady=3)

        self.status_label = ttk.Label(
            status_card,
            text="⚫ Bereit",
            font=("Segoe UI", 12),
            bootstyle="inverse-dark",
            padding=10
        )
        self.status_label.pack(fill=X)

        # Time displays in a frame
        time_display_frame = ttk.Frame(main_frame)
        time_display_frame.pack(fill=X, pady=(0, 5))

        # Current runtime / countdown
        self.time_label = ttk.Label(
            time_display_frame,
            text="Laufzeit: 00:00",
            font=("Segoe UI", 16, "bold"),
            bootstyle="info"
        )
        self.time_label.pack()

        # Countdown remaining (shown when timer active)
        self.countdown_label = ttk.Label(
            time_display_frame,
            text="",
            font=("Segoe UI", 11),
            bootstyle="warning"
        )
        self.countdown_label.pack()

        # Audio level indicator with modern style
        level_frame = ttk.Labelframe(
            main_frame,
            text="🔊 Audio-Pegel",
            padding=5,
            bootstyle="info"
        )
        level_frame.pack(fill=X, pady=(0, 8))

        self.level_meter = ttk.Progressbar(
            level_frame,
            mode='determinate',
            bootstyle="success-striped",
            length=300
        )
        self.level_meter.pack(fill=X)

        # Control buttons with modern styling
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=8, fill=X)

        # Create inner frame for centering buttons
        button_inner = ttk.Frame(button_frame)
        button_inner.pack(anchor=CENTER)

        self.start_button = ttk.Button(
            button_inner,
            text="▶️ Start",
            command=self.start_recording,
            bootstyle="success",
            width=15
        )
        self.start_button.pack(side=LEFT, padx=5)

        self.pause_button = ttk.Button(
            button_inner,
            text="⏸️ Pause",
            command=self.toggle_pause,
            bootstyle="warning",
            width=15,
            state=DISABLED
        )
        self.pause_button.pack(side=LEFT, padx=5)

        self.stop_button = ttk.Button(
            button_inner,
            text="⏹️ Stop",
            command=self.stop_recording,
            bootstyle="danger",
            width=15,
            state=DISABLED
        )
        self.stop_button.pack(side=LEFT, padx=5)

    def on_timer_toggle(self) -> None:
        """Called when timer checkbox is toggled."""
        if self.timer_enabled.get():
            self.update_timer_end_display()

            # If recording is active, apply timer immediately
            if self.is_recording:
                try:
                    minutes = int(self.timer_minutes.get())
                    seconds = int(self.timer_seconds.get())
                    total_seconds = minutes * 60 + seconds

                    if total_seconds > 0:
                        # Set new end time from now
                        self.timer_end_time = datetime.datetime.now() + datetime.timedelta(seconds=total_seconds)
                        logger.info(f"Timer activated during recording: {total_seconds}s from now")
                        self.schedule_timer_stop(total_seconds)
                except ValueError:
                    logger.warning("Invalid timer input during recording")
        else:
            self.timer_end_label.config(text="")
            self.timer_end_time = None

            # If recording is active and timer was disabled, cancel scheduled stop
            if self.is_recording and self.timer_stop_scheduled:
                self.root.after_cancel(self.timer_stop_scheduled)
                self.timer_stop_scheduled = None
                logger.info("Timer disabled during recording - cancelled scheduled stop")

    def schedule_timer_stop(self, seconds: float) -> None:
        """
        Schedule automatic stop after specified seconds.

        Args:
            seconds: Seconds from now when to stop recording
        """
        # Cancel any previously scheduled stop
        if self.timer_stop_scheduled:
            self.root.after_cancel(self.timer_stop_scheduled)

        # Schedule new stop
        milliseconds = int(seconds * 1000)
        self.timer_stop_scheduled = self.root.after(milliseconds, self.stop_recording)
        logger.info(f"Scheduled recording stop in {seconds}s")

    def update_timer_end_display(self) -> None:
        """Update the display showing when timer will end."""
        if not self.timer_enabled.get():
            return

        try:
            minutes = int(self.timer_minutes.get())
            seconds = int(self.timer_seconds.get())
            total_seconds = minutes * 60 + seconds

            if total_seconds > 0:
                end_time = datetime.datetime.now() + datetime.timedelta(seconds=total_seconds)
                self.timer_end_time = end_time
                self.timer_end_label.config(
                    text=f"⏰ Timer endet um: {end_time.strftime('%H:%M:%S')}"
                )
            else:
                self.timer_end_label.config(text="⚠️ Timer-Dauer muss größer als 0 sein")
                self.timer_end_time = None
        except ValueError:
            self.timer_end_label.config(text="⚠️ Ungültige Timer-Eingabe")
            self.timer_end_time = None

    def load_audio_devices(self) -> None:
        """Load available audio devices into combo box."""
        try:
            self.available_devices = AudioRecorder.get_audio_devices()

            if not self.available_devices:
                self.device_combo['values'] = ["Standard (System Loopback)"]
                self.device_combo.current(0)
                logger.warning("No audio devices found, using default")
                return

            # Create display names with loopback indicator
            device_names = []
            default_index = 0

            for i, d in enumerate(self.available_devices):
                loopback_tag = " [Loopback]" if d.get('is_loopback') else " [Mikrofon]"
                default_tag = " ⭐" if d.get('is_default') else ""
                name = f"{d['name']}{loopback_tag}{default_tag}"
                device_names.append(name)

                # Set default loopback as default selection
                if d.get('is_default'):
                    default_index = i

            self.device_combo['values'] = device_names
            self.device_combo.current(default_index)

            loopback_count = sum(1 for d in self.available_devices if d.get('is_loopback'))
            logger.info(f"Loaded {len(self.available_devices)} audio devices ({loopback_count} loopback)")

        except Exception as e:
            logger.error(f"Failed to load audio devices: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Laden der Audio-Geräte:\n{e}")

    def choose_output_folder(self) -> None:
        """Open dialog to choose output folder."""
        folder = filedialog.askdirectory(
            title="Speicherort wählen",
            initialdir=self.output_path
        )

        if folder:
            self.output_path = folder
            self.folder_label.config(text=folder)
            logger.info(f"Output folder changed to: {folder}")

    def get_selected_device(self) -> Optional[dict]:
        """
        Get the selected audio device info.

        Returns:
            Device info dict or None for default device
        """
        try:
            selected_index = self.device_combo.current()

            if selected_index < 0 or selected_index >= len(self.available_devices):
                logger.warning("Invalid device selection, using default")
                return None

            device = self.available_devices[selected_index]
            logger.info(f"Selected device: {device['name']} (loopback={device.get('is_loopback')})")
            return device

        except (IndexError, AttributeError) as e:
            logger.warning(f"Could not get selected device: {e}, using default")
            return None

    def get_selected_bitrate(self) -> int:
        """
        Extract bitrate from quality selection.

        Returns:
            Bitrate in kbps
        """
        selection = self.quality_var.get()  # e.g. "Medium (192 kbps)"
        try:
            # Extract number between parentheses
            bitrate_str = selection.split("(")[1].split(" ")[0]
            return int(bitrate_str)
        except (IndexError, ValueError):
            logger.warning(f"Could not parse bitrate from {selection}, using default")
            return DEFAULT_MP3_BITRATE

    def start_recording(self) -> None:
        """Start audio recording."""
        if self.is_recording:
            return

        try:
            # Get selected device
            device_info = self.get_selected_device()

            # Create new recorder with selected device
            self.recorder = AudioRecorder(device=device_info)

            # Get timer duration
            duration = None
            if self.timer_enabled.get():
                try:
                    minutes = int(self.timer_minutes.get())
                    seconds = int(self.timer_seconds.get())
                    total_seconds = minutes * 60 + seconds

                    if total_seconds <= 0:
                        messagebox.showerror(
                            "Ungültige Eingabe",
                            "Timer-Dauer muss größer als 0 sein."
                        )
                        return

                    duration = total_seconds
                    # Calculate end time
                    self.timer_end_time = datetime.datetime.now() + datetime.timedelta(seconds=duration)

                except ValueError:
                    messagebox.showerror(
                        "Ungültige Eingabe",
                        "Bitte geben Sie gültige Zahlen für den Timer ein."
                    )
                    return

            # Update UI
            self.is_recording = True
            self.is_paused = False
            self.start_time = 0.0
            self.elapsed_time = 0.0

            self.status_label.config(text="🔴 Nehme auf...", bootstyle="danger")
            self.start_button.config(state=DISABLED)
            self.pause_button.config(state=NORMAL)
            self.stop_button.config(state=NORMAL)
            self.device_combo.config(state=DISABLED)
            # Keep timer controls enabled during recording for dynamic adjustment
            # self.timer_minutes.config(state=DISABLED)
            # self.timer_seconds.config(state=DISABLED)
            # self.timer_button.config(state=DISABLED)

            logger.info(f"Starting recording (duration={duration})")

            # Start recording in separate thread
            def record_thread():
                try:
                    self.recorder.start_recording(
                        duration=duration,
                        callback=self.on_recording_progress
                    )
                    # Recording finished normally (timer expired)
                    if self.is_recording:
                        self.root.after(0, self.stop_recording)
                except AudioRecorderError as e:
                    logger.error(f"Recording error: {e}")
                    error_msg = str(e)
                    self.root.after(0, lambda msg=error_msg: self.on_recording_error(msg))

            Thread(target=record_thread, daemon=True).start()

            # Start UI updates
            self.update_display()
            self.update_audio_level()

        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            messagebox.showerror("Fehler", f"Aufnahme konnte nicht gestartet werden:\n{e}")
            self.reset_ui()

    def toggle_pause(self) -> None:
        """Toggle pause/resume recording."""
        if not self.is_recording:
            return

        if self.is_paused:
            # Resume
            self.recorder.resume_recording()
            self.is_paused = False
            self.pause_button.config(text="⏸️ Pause")
            self.status_label.config(text="🔴 Nehme auf...", bootstyle="danger")
            logger.info("Recording resumed")
        else:
            # Pause
            self.recorder.pause_recording()
            self.is_paused = True
            self.pause_button.config(text="▶️ Fortsetzen")
            self.status_label.config(text="⏸️ Pausiert", bootstyle="warning")
            logger.info("Recording paused")

    def stop_recording(self) -> None:
        """Stop recording and save file."""
        if not self.is_recording:
            return

        try:
            # Stop recording
            self.recorder.stop_recording()
            self.is_recording = False
            self.is_paused = False

            # Update UI
            self.status_label.config(text="💾 Speichere...", bootstyle="info")
            self.pause_button.config(state=DISABLED)
            self.stop_button.config(state=DISABLED)

            # Save and encode in separate thread
            def save_thread():
                try:
                    # Generate filename
                    timestamp = datetime.datetime.now().strftime(TIMESTAMP_FORMAT)
                    wav_file = os.path.join(self.output_path, f"temp_{timestamp}.wav")
                    mp3_file = os.path.join(self.output_path, f"{OUTPUT_FILE_PREFIX}{timestamp}.mp3")

                    # Ensure output folder exists
                    os.makedirs(self.output_path, exist_ok=True)

                    # Save to WAV
                    self.recorder.save_to_wav(wav_file)

                    # Encode to MP3
                    bitrate = self.get_selected_bitrate()
                    self.encoder = MP3Encoder(bitrate=bitrate)
                    self.encoder.convert_wav_to_mp3(wav_file, mp3_file, delete_wav=True)

                    # Success
                    saved_file = mp3_file
                    self.root.after(0, lambda file=saved_file: self.on_save_success(file))

                except (AudioRecorderError, MP3EncoderError) as e:
                    logger.error(f"Save error: {e}")
                    error_msg = str(e)
                    self.root.after(0, lambda msg=error_msg: self.on_save_error(msg))
                finally:
                    # Clean up WAV file if it still exists
                    if os.path.exists(wav_file):
                        try:
                            os.remove(wav_file)
                        except Exception as e:
                            logger.warning(f"Failed to delete temp WAV: {e}")

            Thread(target=save_thread, daemon=True).start()

        except Exception as e:
            logger.error(f"Failed to stop recording: {e}")
            messagebox.showerror("Fehler", f"Fehler beim Stoppen:\n{e}")
            self.reset_ui()

    def on_recording_progress(self, elapsed: float) -> None:
        """
        Callback for recording progress.

        Args:
            elapsed: Elapsed time in seconds
        """
        self.elapsed_time = elapsed

    def on_recording_error(self, error_msg: str) -> None:
        """
        Handle recording error.

        Args:
            error_msg: Error message
        """
        self.is_recording = False
        messagebox.showerror("Aufnahmefehler", f"Fehler bei der Aufnahme:\n{error_msg}")
        self.reset_ui()

    def on_save_success(self, filename: str) -> None:
        """
        Handle successful save.

        Args:
            filename: Path to saved file
        """
        file_size_mb = os.path.getsize(filename) / (1024 * 1024)
        self.status_label.config(
            text=f"✅ Gespeichert: {os.path.basename(filename)}",
            bootstyle="success"
        )
        messagebox.showinfo(
            "Fertig",
            f"Aufnahme erfolgreich gespeichert!\n\n"
            f"Datei: {os.path.basename(filename)}\n"
            f"Größe: {file_size_mb:.2f} MB\n"
            f"Ort: {self.output_path}"
        )
        self.reset_ui()
        logger.info(f"Recording saved successfully: {filename}")

    def on_save_error(self, error_msg: str) -> None:
        """
        Handle save error.

        Args:
            error_msg: Error message
        """
        self.status_label.config(text="❌ Fehler beim Speichern", bootstyle="danger")
        messagebox.showerror("Speicherfehler", f"Fehler beim Speichern:\n{error_msg}")
        self.reset_ui()

    def update_display(self) -> None:
        """Update time display and countdown."""
        if self.is_recording:
            # Show elapsed time
            mins, secs = divmod(int(self.elapsed_time), 60)
            self.time_label.config(text=f"Laufzeit: {mins:02d}:{secs:02d}")

            # Show countdown if timer is active
            if self.timer_enabled.get() and self.timer_end_time:
                remaining = (self.timer_end_time - datetime.datetime.now()).total_seconds()
                if remaining > 0:
                    remaining_mins, remaining_secs = divmod(int(remaining), 60)
                    self.countdown_label.config(
                        text=f"⏱️ Verbleibend: {remaining_mins:02d}:{remaining_secs:02d}"
                    )
                else:
                    self.countdown_label.config(text="⏱️ Timer abgelaufen")
            else:
                self.countdown_label.config(text="")

            self.root.after(TIMER_DISPLAY_INTERVAL_MS, self.update_display)
        else:
            self.time_label.config(text="Laufzeit: 00:00")
            self.countdown_label.config(text="")

    def update_audio_level(self) -> None:
        """Update audio level indicator."""
        if self.is_recording and not self.is_paused:
            try:
                level = self.recorder.get_audio_level()
                # Update progress bar (0-100)
                self.level_meter['value'] = level * 100

                # Change color based on level
                if level > 0.9:
                    self.level_meter.config(bootstyle="danger-striped")
                elif level > 0.7:
                    self.level_meter.config(bootstyle="warning-striped")
                else:
                    self.level_meter.config(bootstyle="success-striped")

            except Exception as e:
                logger.error(f"Failed to update audio level: {e}")

            self.root.after(100, self.update_audio_level)
        else:
            # Reset level meter
            self.level_meter['value'] = 0

    def reset_ui(self) -> None:
        """Reset UI to initial state."""
        self.is_recording = False
        self.is_paused = False
        self.timer_end_time = None

        # Cancel any scheduled timer stop
        if self.timer_stop_scheduled:
            self.root.after_cancel(self.timer_stop_scheduled)
            self.timer_stop_scheduled = None

        self.status_label.config(text="⚫ Bereit", bootstyle="dark")
        self.start_button.config(state=NORMAL)
        self.pause_button.config(state=DISABLED, text="⏸️ Pause")
        self.stop_button.config(state=DISABLED)
        self.device_combo.config(state="readonly")
        self.timer_minutes.config(state=NORMAL)
        self.timer_seconds.config(state=NORMAL)
        self.timer_button.config(state=NORMAL)
        self.time_label.config(text="Laufzeit: 00:00")
        self.countdown_label.config(text="")
        self.level_meter['value'] = 0

        # Update timer end display if still enabled
        if self.timer_enabled.get():
            self.update_timer_end_display()
