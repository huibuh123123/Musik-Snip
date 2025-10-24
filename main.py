"""
Musik-Snip - System Audio Recorder
A simple GUI application for recording system audio and converting to MP3.

Author: Created with Claude Code
License: MIT
"""

import sys
import logging
from tkinter import messagebox

import ttkbootstrap as ttk

from gui import AudioRecorderGUI
from config import GUI_THEME


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('audio_recorder.log'),
            logging.StreamHandler()
        ]
    )


def check_dependencies():
    """
    Check if all required dependencies are installed.

    Returns:
        True if all dependencies are available, False otherwise
    """
    required_modules = {
        'pyaudiowpatch': 'pyaudiowpatch',
        'soundfile': 'soundfile',
        'numpy': 'numpy',
        'lameenc': 'lameenc',
        'ttkbootstrap': 'ttkbootstrap'
    }

    missing = []

    for module_name, pip_name in required_modules.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(pip_name)

    if missing:
        error_msg = (
            "Die folgenden erforderlichen Module fehlen:\n\n"
            + "\n".join(f"  - {m}" for m in missing)
            + "\n\nBitte installieren Sie sie mit:\n"
            + f"pip install {' '.join(missing)}"
        )
        messagebox.showerror("Fehlende Abhängigkeiten", error_msg)
        return False

    return True


def main():
    """Main entry point for the application."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("Starting Musik-Snip Audio Recorder")

    # Check dependencies
    if not check_dependencies():
        logger.error("Missing dependencies, exiting")
        sys.exit(1)

    try:
        # Create main window with modern theme
        root = ttk.Window(themename=GUI_THEME)

        # Create GUI
        app = AudioRecorderGUI(root)

        # Handle window close
        def on_closing():
            if app.is_recording:
                if messagebox.askokcancel(
                    "Aufnahme läuft",
                    "Eine Aufnahme ist noch aktiv. Wirklich beenden?"
                ):
                    app.recorder.stop_recording()
                    root.destroy()
            else:
                root.destroy()

        root.protocol("WM_DELETE_WINDOW", on_closing)

        logger.info("Application started successfully")

        # Start main loop
        root.mainloop()

    except Exception as e:
        logger.critical(f"Application crashed: {e}", exc_info=True)
        messagebox.showerror(
            "Kritischer Fehler",
            f"Die Anwendung ist abgestürzt:\n{e}\n\n"
            "Bitte prüfen Sie die Log-Datei für Details."
        )
        sys.exit(1)

    logger.info("Application closed")


if __name__ == "__main__":
    main()
