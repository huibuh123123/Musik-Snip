import tkinter as tk
from tkinter import messagebox
import sounddevice as sd
import soundfile as sf
import numpy as np
import threading
import time
import datetime
import lameenc
import os

class AudioRecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎙️ System Audio Recorder")
        self.root.geometry("420x300")
        self.root.resizable(False, False)

        # Aufnahmeparameter
        self.samplerate = 44100
        self.channels = 2
        self.is_recording = False
        self.stop_flag = False
        self.start_time = None
        self.timer_enabled = tk.BooleanVar(value=False)

        # GUI
        tk.Label(root, text="System Audio Recorder", font=("Arial", 16, "bold")).pack(pady=10)

        frame_time = tk.Frame(root)
        frame_time.pack()

        tk.Label(frame_time, text="Timer (Minuten):", font=("Arial", 12)).grid(row=0, column=0, padx=5)
        self.entry_time = tk.Entry(frame_time, width=6, font=("Arial", 12), justify="center")
        self.entry_time.insert(0, "5")
        self.entry_time.grid(row=0, column=1)

        tk.Checkbutton(frame_time, text="Timer aktivieren", variable=self.timer_enabled, font=("Arial", 10)).grid(row=1, column=0, columnspan=2, pady=5)

        self.status_label = tk.Label(root, text="Bereit.", font=("Arial", 11), fg="gray")
        self.status_label.pack(pady=5)

        self.time_label = tk.Label(root, text="Laufzeit: 00:00", font=("Arial", 12))
        self.time_label.pack()

        # Buttons
        frame_buttons = tk.Frame(root)
        frame_buttons.pack(pady=10)

        self.start_button = tk.Button(frame_buttons, text="▶️ Start", font=("Arial", 12), bg="#4CAF50", fg="white", width=10, command=self.start_recording)
        self.start_button.grid(row=0, column=0, padx=10)

        self.stop_button = tk.Button(frame_buttons, text="⏹️ Stop", font=("Arial", 12), bg="#E53935", fg="white", width=10, state="disabled", command=self.stop_recording)
        self.stop_button.grid(row=0, column=1, padx=10)

    # Aufnahme starten
    def start_recording(self):
        if self.is_recording:
            return

        self.is_recording = True
        self.stop_flag = False
        self.start_time = time.time()
        self.status_label.config(text="Nehme auf...", fg="red")
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

        # Timer-Dauer (optional)
        try:
            duration_minutes = int(self.entry_time.get())
        except ValueError:
            duration_minutes = 0

        duration = duration_minutes * 60 if self.timer_enabled.get() and duration_minutes > 0 else None

        threading.Thread(target=self.record_audio, args=(duration,), daemon=True).start()
        self.update_runtime()

    # Laufzeitanzeige aktualisieren
    def update_runtime(self):
        if self.is_recording and not self.stop_flag:
            elapsed = int(time.time() - self.start_time)
            mins, secs = divmod(elapsed, 60)
            self.time_label.config(text=f"Laufzeit: {mins:02d}:{secs:02d}")
            self.root.after(1000, self.update_runtime)
        elif not self.is_recording:
            self.time_label.config(text="Laufzeit: 00:00")

    # Aufnahme stoppen
    def stop_recording(self):
        if not self.is_recording:
            return
        self.stop_flag = True
        self.status_label.config(text="Beende Aufnahme...", fg="orange")

    # Aufnahme durchführen
    def record_audio(self, duration):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        wav_filename = f"temp_{timestamp}.wav"
        mp3_filename = f"aufnahme_{timestamp}.mp3"

        # Aufnahme starten
        print("Starte Aufnahme...")
        frames = []
        blocksize = 1024

        def callback(indata, frames_count, time_info, status):
            if self.stop_flag:
                raise sd.CallbackStop
            frames.append(indata.copy())

        with sd.InputStream(samplerate=self.samplerate, channels=self.channels, dtype='float32', callback=callback):
            start = time.time()
            while not self.stop_flag:
                if duration and (time.time() - start) >= duration:
                    break
                time.sleep(0.1)

        # Speichern
        data = np.concatenate(frames, axis=0)
        sf.write(wav_filename, data, self.samplerate)

        # In MP3 umwandeln
        encoder = lameenc.Encoder()
        encoder.set_bit_rate(192)
        encoder.set_in_sample_rate(self.samplerate)
        encoder.set_channels(self.channels)
        encoder.set_quality(2)
        pcm_data = (data * 32767).astype(np.int16).tobytes()
        mp3_data = encoder.encode(pcm_data) + encoder.flush()
        with open(mp3_filename, "wb") as f:
            f.write(mp3_data)

        os.remove(wav_filename)
        print(f"Gespeichert: {mp3_filename}")

        # UI zurücksetzen
        self.is_recording = False
        self.stop_flag = False
        self.status_label.config(text=f"Gespeichert: {mp3_filename}", fg="green")
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        messagebox.showinfo("Fertig", f"Aufnahme gespeichert als:\n{mp3_filename}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioRecorderApp(root)
    root.mainloop()
