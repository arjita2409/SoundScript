import tkinter as tk
import threading
import speech_recognition as sr
from deep_translator import GoogleTranslator
from langdetect import detect
from gtts import gTTS
import os
import sounddevice as sd
from scipy.io.wavfile import write
import pygame
import time

# ================= INIT =================
recognizer = sr.Recognizer()
pygame.mixer.init()

speaker_languages = {}
running = False

# ================= AUDIO =================
def record_audio(filename="input.wav", duration=4, fs=44100):
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()
    write(filename, fs, recording)

def speak(text, lang):
    try:
        tts = gTTS(text=text, lang=lang)
        filename = "output.mp3"
        tts.save(filename)

        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            continue

        pygame.mixer.music.unload()
        os.remove(filename)
    except:
        add_message("⚠️ Speech error", "system")

# ================= LANGUAGE =================
def detect_language(text):
    text_lower = text.lower()

    hindi_words = [
        "main", "tum", "kya", "kaise", "nahi", "haan",
        "raha", "rahe", "rahi", "kar", "ho", "hai",
        "hun", "mera", "teri", "kuchh"
    ]

    # Devanagari
    if any('\u0900' <= c <= '\u097F' for c in text):
        return "hi"

    # Hinglish
    if any(word in text_lower for word in hindi_words):
        return "hi"

    try:
        lang = detect(text)
        if lang in ["en", "hi", "fr", "es", "de"]:
            return lang
        else:
            return "en"
    except:
        return "en"

def translate_text(text, target):
    try:
        return GoogleTranslator(source='auto', target=target).translate(text)
    except:
        return "Translation Error"

# ================= SPEAKER =================
def get_speaker(lang):
    if lang not in speaker_languages.values() and len(speaker_languages) < 2:
        speaker_id = len(speaker_languages) + 1
        speaker_languages[f"Person {speaker_id}"] = lang
        add_message(f"🧠 Person {speaker_id} set as {lang.upper()}", "system")

    for person, l in speaker_languages.items():
        if l == lang:
            return person

    return None

# ================= CHAT UI =================
def add_message(text, sender="system"):
    frame = tk.Frame(scrollable_frame, bg="#f5f5f5")

    if sender == "Person 1":
        msg = tk.Label(frame, text=text, bg="#d1e7dd", wraplength=300,
                       justify="left", padx=10, pady=5)
        msg.pack(anchor="w", padx=10, pady=5)

    elif sender == "Person 2":
        msg = tk.Label(frame, text=text, bg="#cfe2ff", wraplength=300,
                       justify="left", padx=10, pady=5)
        msg.pack(anchor="e", padx=10, pady=5)

    else:
        msg = tk.Label(frame, text=text, bg="#eeeeee",
                       wraplength=300, justify="center", padx=10, pady=5)
        msg.pack(anchor="center", pady=5)

    frame.pack(fill="both", expand=True)
    canvas.update_idletasks()
    canvas.yview_moveto(1)

# ================= MAIN LOOP =================
def listen_loop():
    global running

    while running:
        try:
            add_message("🎤 Listening...", "system")

            record_audio()

            with sr.AudioFile("input.wav") as source:
                audio = recognizer.record(source)

            text = recognizer.recognize_google(audio)

            if len(text.strip()) < 3:
                continue

            lang = detect_language(text)
            person = get_speaker(lang)

            if person is None:
                continue

            add_message(f"{person}: {text}", person)

            if len(speaker_languages) < 2:
                translated = translate_text(text, "en")
                add_message(f"🌐 {translated}", "system")
                speak(translated, "en")

            else:
                langs = list(speaker_languages.values())
                target = langs[1] if lang == langs[0] else langs[0]

                translated = translate_text(text, target)
                add_message(f"🌐 {translated}", "system")
                speak(translated, target)

            time.sleep(1)

        except:
            continue

# ================= CONTROL =================
def start():
    global running
    if not running:
        running = True
        add_message("🚀 Conversation Started", "system")
        threading.Thread(target=listen_loop, daemon=True).start()

def stop():
    global running
    running = False
    add_message("⏹️ Stopped", "system")

def reset():
    global running
    running = False
    speaker_languages.clear()
    add_message("🔄 Reset Done", "system")

# ================= UI =================
root = tk.Tk()
root.title("AI Conversation Translator")
root.geometry("520x650")
root.configure(bg="#f5f5f5")

display_frame = tk.Frame(root, bg="#f5f5f5")
display_frame.pack(fill=tk.BOTH, expand=True)

canvas = tk.Canvas(display_frame, bg="#f5f5f5")
scrollbar = tk.Scrollbar(display_frame, command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg="#f5f5f5")

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Buttons
btn_frame = tk.Frame(root, bg="#ffffff")
btn_frame.pack(pady=10)

start_btn = tk.Button(btn_frame, text="▶ Start", command=start,
                      bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), width=10)
start_btn.pack(side=tk.LEFT, padx=10)

stop_btn = tk.Button(btn_frame, text="⏸ Stop", command=stop,
                     bg="#ff9800", fg="white", font=("Arial", 12, "bold"), width=10)
stop_btn.pack(side=tk.LEFT, padx=10)

reset_btn = tk.Button(btn_frame, text="🔄 Reset", command=reset,
                      bg="#f44336", fg="white", font=("Arial", 12, "bold"), width=10)
reset_btn.pack(side=tk.LEFT, padx=10)

root.mainloop()