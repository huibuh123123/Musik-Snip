"""
GUI for the Audio Recorder application.
"""

import os
import logging
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from threading import Thread
from typing import Optional

from config import (
    WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_RESIZABLE,
    COLOR_START_BUTTON, COLOR_STOP_BUTTON, COLOR_PAUSE_BUTTON,
    COLOR_RECORDING, COLOR_READY, COLOR_SUCCESS, COLOR_ERROR, COLOR_WARNING,
    DEFAULT_TIMER_MINUTES, TIMER_DISPLAY_INTERVAL_MS,
    MP3_BITRATE_OPTIONS, DEFAULT_MP3_BITRATE,
    OUTPUT_FOLDER, OUTPUT_FILE_PREFIX, TIMESTAMP_FORMAT
)
from recorder import AudioRecorder, AudioRecorderError
from encoder import MP3Encoder, MP3EncoderError


logger = logging.getLogger(__name__)


class AudioRecorderGUI:
    """
    Main GUI class for the Audio Recorder application.
    """

    def __init__(self, root: tk.Tk):
        """
        Initialize the GUI.

        Args:
            root: Tkinter root window
        """
        self.root = root
        self.recorder = AudioRecorder()
        self.encoder: Optional[MP3Encoder] = None

        # State variables
        self.is_recording = False
        self.is_paused = False
        self.start_time = 0.0
        self.elapsed_time = 0.0
        self.output_path = OUTPUT_FOLDER

        # Setup window
        self.setup_window()

        # Create GUI elements
        self.create_widgets()

        # Load audio devices
        self.load_audio_devices()

        logger.info("GUI initialized")

    def setup_window(self) -> None:
        """Configure the main window."""
        self.root.title(WINDOW_TITLE)
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(WINDOW_RESIZABLE, WINDOW_RESIZABLE)

    def create_widgets(self) -> None:
        """Create all GUI widgets."""
        # Title
        title_label = tk.Label(
            self.root,
            text="System Audio Recorder",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=10)

        # Device selection frame
        device_frame = tk.LabelFrame(self.root, text="Audio-Gerät", font=("Arial", 10))
        device_frame.pack(padx=20, pady=5, fill="x")

        self.device_var = tk.StringVar()
        self.device_combo = ttk.Combobox(
            device_frame,
            textvariable=self.device_var,
            state="readonly",
            font=("Arial", 10)
        )
        self.device_combo.pack(padx=10, pady=5, fill="x")

        # Settings frame
        settings_frame = tk.LabelFrame(self.root, text="Einstellungen", font=("Arial", 10))
        settings_frame.pack(padx=20, pady=5, fill="x")

        # Timer settings
        timer_frame = tk.Frame(settings_frame)
        timer_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(timer_frame, text="Timer (Minuten):", font=("Arial", 10)).pack(side="left")
        self.timer_entry = tk.Entry(timer_frame, width=8, font=("Arial", 10), justify="center")
        self.timer_entry.insert(0, str(DEFAULT_TIMER_MINUTES))
        self.timer_entry.pack(side="left", padx=10)

        self.timer_enabled = tk.BooleanVar(value=False)
        tk.Checkbutton(
            timer_frame,
            text="Timer aktivieren",
            variable=self.timer_enabled,
            font=("Arial", 10)
        ).pack(side="left", padx=10)

        # Quality settings
        quality_frame = tk.Frame(settings_frame)
        quality_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(quality_frame, text="MP3-Qualität:", font=("Arial", 10)).pack(side="left")
        self.quality_var = tk.StringVar(value="Medium")
        quality_combo = ttk.Combobox(
            quality_frame,
            textvariable=self.quality_var,
            values=list(MP3_BITRATE_OPTIONS.keys()),
            state="readonly",
            width=12,
            font=("Arial", 10)
        )
        quality_combo.pack(side="left", padx=10)

        # Output folder selection
        folder_frame = tk.Frame(settings_frame)
        folder_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(folder_frame, text="Speicherort:", font=("Arial", 10)).pack(side="left")
        self.folder_label = tk.Label(
            folder_frame,
            text=OUTPUT_FOLDER,
            font=("Arial", 9),
            fg="blue",
            cursor="hand2"
        )
        self.folder_label.pack(side="left", padx=10)
        self.folder_label.bind("<Button-1>", lambda e: self.choose_output_folder())

        tk.Button(
            folder_frame,
            text="Ändern",
            command=self.choose_output_folder,
            font=("Arial", 9)
        ).pack(side="left")

        # Status display
        status_frame = tk.Frame(self.root)
        status_frame.pack(pady=10)

        self.status_label = tk.Label(
            status_frame,
            text="Bereit",
            font=("Arial", 11),
            fg=COLOR_READY
        )
        self.status_label.pack()

        self.time_label = tk.Label(
            status_frame,
            text="Laufzeit: 00:00",
            font=("Arial", 12, "bold")
        )
        self.time_label.pack(pady=5)

        # Audio level indicator
        self.level_canvas = tk.Canvas(self.root, height=20, bg="white")
        self.level_canvas.pack(padx=20, pady=5, fill="x")
        self.level_bar = self.level_canvas.create_rectangle(
            0, 0, 0, 20,
            fill="green",
            outline=""
        )

        # Control buttons
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        self.start_button = tk.Button(
            button_frame,
            text="Start",
            font=("Arial", 12, "bold"),
            bg=COLOR_START_BUTTON,
            fg="white",
            width=10,
            command=self.start_recording
        )
        self.start_button.grid(row=0, column=0, padx=5)

        self.pause_button = tk.Button(
            button_frame,
            text="Pause",
            font=("Arial", 12, "bold"),
            bg=COLOR_PAUSE_BUTTON,
            fg="white",
            width=10,
            state="disabled",
            command=self.toggle_pause
        )
        self.pause_button.grid(row=0, column=1, padx=5)

        self.stop_button = tk.Button(
            button_frame,
            text="Stop",
            font=("Arial", 12, "bold"),
            bg=COLOR_STOP_BUTTON,
            fg="white",
            width=10,
            state="disabled",
            command=self.stop_recording
        )
        self.stop_button.grid(row=0, column=2, padx=5)

    def load_audio_devices(self) -> None:
        """Load available audio devices into combo box."""
        try:
            devices = AudioRecorder.get_audio_devices()

            if not devices:
                self.device_combo['values'] = ["Standard (System Default)"]
                self.device_combo.current(0)
                logger.warning("No audio devices found, using default")
                return

            device_names = [f"{d['name']} (ID: {d['id']})" for d in devices]
            device_names.insert(0, "Standard (System Default)")

            self.device_combo['values'] = device_names
            self.device_combo.current(0)

            logger.info(f"Loaded {len(devices)} audio devices")

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

    def get_selected_device(self) -> Optional[int]:
        """
        Get the selected audio device ID.

        Returns:
            Device ID or None for default device
        """
        selection = self.device_var.get()
        if "Standard" in selection:
            return None

        try:
            # Extract device ID from selection string
            device_id = int(selection.split("ID: ")[1].rstrip(")"))
            return device_id
        except (IndexError, ValueError):
            logger.warning("Could not parse device ID, using default")
            return None

    def start_recording(self) -> None:
        """Start audio recording."""
        if self.is_recording:
            return

        try:
            # Get selected device
            device_id = self.get_selected_device()

            # Create new recorder with selected device
            self.recorder = AudioRecorder(device=device_id)

            # Get timer duration
            duration = None
            if self.timer_enabled.get():
                try:
                    minutes = int(self.timer_entry.get())
                    if minutes <= 0:
                        raise ValueError("Timer must be positive")
                    duration = minutes * 60
                except ValueError as e:
                    messagebox.showerror(
                        "Ungültige Eingabe",
                        "Bitte geben Sie eine gültige Zeitdauer ein (positive Ganzzahl)."
                    )
                    return

            # Update UI
            self.is_recording = True
            self.is_paused = False
            self.start_time = 0.0
            self.elapsed_time = 0.0

            self.status_label.config(text="Nehme auf...", fg=COLOR_RECORDING)
            self.start_button.config(state="disabled")
            self.pause_button.config(state="normal")
            self.stop_button.config(state="normal")
            self.device_combo.config(state="disabled")

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
                    self.root.after(0, lambda: self.on_recording_error(str(e)))

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
            self.pause_button.config(text="Pause")
            self.status_label.config(text="Nehme auf...", fg=COLOR_RECORDING)
            logger.info("Recording resumed")
        else:
            # Pause
            self.recorder.pause_recording()
            self.is_paused = True
            self.pause_button.config(text="Fortsetzen")
            self.status_label.config(text="Pausiert", fg=COLOR_WARNING)
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
            self.status_label.config(text="Speichere...", fg=COLOR_WARNING)
            self.pause_button.config(state="disabled")
            self.stop_button.config(state="disabled")

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
                    bitrate = MP3_BITRATE_OPTIONS[self.quality_var.get()]
                    self.encoder = MP3Encoder(bitrate=bitrate)
                    self.encoder.convert_wav_to_mp3(wav_file, mp3_file, delete_wav=True)

                    # Success
                    self.root.after(0, lambda: self.on_save_success(mp3_file))

                except (AudioRecorderError, MP3EncoderError) as e:
                    logger.error(f"Save error: {e}")
                    self.root.after(0, lambda: self.on_save_error(str(e)))
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
            text=f"Gespeichert: {os.path.basename(filename)} ({file_size_mb:.1f} MB)",
            fg=COLOR_SUCCESS
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
        self.status_label.config(text="Fehler beim Speichern", fg=COLOR_ERROR)
        messagebox.showerror("Speicherfehler", f"Fehler beim Speichern:\n{error_msg}")
        self.reset_ui()

    def update_display(self) -> None:
        """Update time display."""
        if self.is_recording:
            mins, secs = divmod(int(self.elapsed_time), 60)
            self.time_label.config(text=f"Laufzeit: {mins:02d}:{secs:02d}")
            self.root.after(TIMER_DISPLAY_INTERVAL_MS, self.update_display)
        else:
            self.time_label.config(text="Laufzeit: 00:00")

    def update_audio_level(self) -> None:
        """Update audio level indicator."""
        if self.is_recording and not self.is_paused:
            try:
                level = self.recorder.get_audio_level()
                canvas_width = self.level_canvas.winfo_width()
                bar_width = int(canvas_width * level)

                self.level_canvas.coords(self.level_bar, 0, 0, bar_width, 20)

                # Change color based on level
                if level > 0.9:
                    color = "red"
                elif level > 0.7:
                    color = "orange"
                else:
                    color = "green"

                self.level_canvas.itemconfig(self.level_bar, fill=color)

            except Exception as e:
                logger.error(f"Failed to update audio level: {e}")

            self.root.after(100, self.update_audio_level)
        else:
            # Reset level bar
            self.level_canvas.coords(self.level_bar, 0, 0, 0, 20)

    def reset_ui(self) -> None:
        """Reset UI to initial state."""
        self.is_recording = False
        self.is_paused = False
        self.status_label.config(text="Bereit", fg=COLOR_READY)
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled", text="Pause")
        self.stop_button.config(state="disabled")
        self.device_combo.config(state="readonly")
        self.time_label.config(text="Laufzeit: 00:00")
        self.level_canvas.coords(self.level_bar, 0, 0, 0, 20)
