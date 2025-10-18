import os
import webbrowser
import google.generativeai as genai
import wikipedia
import math
import ctypes
import threading
import csv
import pandas as pd
import inflect
import pyttsx3
import time
import pyautogui
from datetime import datetime
from dotenv import load_dotenv
import speech_recognition as sr
from kivy.config import Config

# Kivy Config
Config.set('graphics', 'borderless', '1')
Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'width', '1920')
Config.set('graphics', 'height', '1080')

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.core.window import Window
from kivy.animation import Animation
from queue import Queue

# Hinglish commands mapping
HINGLISH_COMMANDS = {
    "time kya hai": "what is the time",
    "computer band karo": "shutdown",
    "browser kholo": "open chrome",
    "gaana chalao": "play music",
    "wikipedia search karo": "search wikipedia",
    "system restart karo": "restart",
    "lock screen": "lock",
    "calculator kholo": "open calculator",
    "paint kholo": "open paint",
    "file explorer kholo": "open file explorer"
}

# Window setup
Window.size = (1920, 1080)
Window.top = 0
Window.left = 0
Window.borderless = True

# ================= API KEY SETUP ==================
# Directly set your Gemini API key here
genai.api_key = "AIzaSyBYiXBrhnO4mq0ILtmxXP_oi4xuvFjmrj0"

recognizer = sr.Recognizer()
muted = False
p = inflect.engine()

#  Load Q&A Data from Excel 
qa_file_path = "qa_1000.xlsx"  # Make sure this file is in the same folder as your script
qa_data = {}

try:
    df = pd.read_excel(qa_file_path)
    for _, row in df.iterrows():
        question = str(row["Question"]).strip().lower()
        answer = str(row["Answer"]).strip()
        qa_data[question] = answer
    print(f"Loaded {len(qa_data)} Q&A pairs from {qa_file_path}")
except FileNotFoundError:
    print(f"⚠️ Q&A file '{qa_file_path}' not found. Q&A feature disabled.")
    qa_data = {}

# Speech queue and worker thread
speech_queue = Queue()

def speech_worker():
    engine = pyttsx3.init()
    engine.setProperty('rate', 160)
    engine.setProperty('volume', 1.0)
    while True:
        text = speech_queue.get()
        if text is None:
            break
        engine.say(text)
        engine.runAndWait()

threading.Thread(target=speech_worker, daemon=True).start()

def speak(text):
    if not muted:
        # Hinglish-style auto reply for some commands
        hinglish_replies = {
            "what is the time": f"Abhi ka time hai {datetime.now().strftime('%I:%M %p')}",
            "shutdown": "Thik hai, system abhi band ho raha hai.",
            "open chrome": "Chrome khol raha hoon.",
            "play music": "Gaana chala raha hoon.",
            "search wikipedia": "Wikipedia pe search kar raha hoon.",
            "restart": "System restart ho raha hai.",
            "lock": "Screen abhi lock ho rahi hai."
        }
        if text.lower() in hinglish_replies:
            text = hinglish_replies[text.lower()]

        print(f"\nShubhavi: {text}\n")
        speech_queue.put(text)

def get_voice_input():
    with sr.Microphone() as src:
        recognizer.adjust_for_ambient_noise(src)
        audio = recognizer.listen(src)

    text = ""
    try:
        # First try English (Indian accent)
        text = recognizer.recognize_google(audio, language="en-IN").lower()
        print(f"You (Voice-English): {text}")
    except sr.UnknownValueError:
        try:
            # Then try Hindi (for Hinglish)
            text = recognizer.recognize_google(audio, language="hi-IN").lower()
            print(f"You (Voice-Hindi): {text}")
        except:
            speak("Sorry, I didn’t catch that.")
            return ""

    # Translate Hinglish to English commands if found
    for hinglish, english in HINGLISH_COMMANDS.items():
        if hinglish in text:
            text = english
            break

    return text

def ask_gemini(prompt):
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        else:
            return "Sorry, I couldn’t find an answer."
    except Exception as e:
        return f"Error while contacting Gemini: {e}"


def handle_input(cmd):
    global muted
    cmd = cmd.strip().lower()
    if not cmd:
        return

    if cmd in qa_data:
        speak(qa_data[cmd])

    elif any(word in cmd for word in ["you are smart", "you are like human", "appreciate", "good", "nice", "awesome"]):
        speak("Thank you! I really appreciate your kind words.")
    elif cmd in ["who is your inventor"]:
        speak("Aradhya is my boss.")
    elif cmd in ["exit", "bye", "shutdown yourself", "close yourself"]:
        speak("Shutting myself down.")
        os._exit(0)
    elif cmd in ["hi", "hello", "hey"]:
        speak("Namaste! How can I help you?")
    elif cmd in ["how are you"]:
        speak("I’m great and ready to assist!")
    elif cmd in ["what is your name", "who are you"]:
        speak("I am Shubhavi, your smart assistant.")
    elif cmd == "mute":
        muted = True
    elif cmd == "unmute":
        muted = False
    elif "time" in cmd:
        speak("The time is " + datetime.now().strftime("%I:%M %p"))
    elif "date" in cmd:
        speak("Today is " + datetime.now().strftime("%A, %d %B %Y"))
    elif "shutdown" in cmd:
        speak("Shutting down PC.")
        os.system("shutdown /s /t 1")
    elif "restart" in cmd:
        speak("Restarting PC.")
        os.system("shutdown /r /t 1")
    elif "lock" in cmd:
        speak("Locking PC.")
        try:
            ctypes.windll.user32.LockWorkStation()
        except:
            speak("Unable to lock the PC.")
    elif cmd.startswith("open notepad and write"):
        speak("Opening Notepad. Please wait.")
        os.system("start notepad")
        time.sleep(2)

        text = cmd.replace("open notepad and write", "").strip()

        if not text:
            speak("What should I write?")
            text = get_voice_input()

        pyautogui.write(text, interval=0.05)
        speak("Written successfully.")
    elif "open word and write" in cmd:
        word_path = r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE"
        if os.path.exists(word_path):
            speak("Opening Word. Please wait.")
            os.startfile(word_path)
            time.sleep(5)
            speak("What should I write?")
            text = get_voice_input()
            pyautogui.write(text, interval=0.05)
        else:
            speak("Microsoft Word is not installed or the path is incorrect.")
    elif "open notepad" in cmd:
        os.system("start notepad")
        speak("Opening Notepad")
    elif "open calculator" in cmd:
        os.system("start calc")
        speak("Opening Calculator")
    elif "open paint" in cmd:
        os.system("start mspaint")
        speak("Opening Paint")
    elif "open file explorer" in cmd:
        os.system("start explorer")
        speak("Opening File Explorer")
    elif "open command prompt" in cmd or "open cmd" in cmd:
        os.system("start cmd")
        speak("Opening Command Prompt")
    elif "open vlc" in cmd:
        vlc = "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe"
        if os.path.exists(vlc):
            os.startfile(vlc)
            speak("Opening VLC")
        else:
            speak("VLC is not installed.")
    elif "open chrome" in cmd:
        ch = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        if os.path.exists(ch):
            os.startfile(ch)
            speak("Opening Chrome")
        else:
            speak("Chrome is not installed.")
    elif cmd in ["start minecraft", "launch minecraft", "play minecraft"]:
        tla_path = os.path.expandvars(r"%USERPROFILE%\AppData\Roaming\.minecraft\TLauncher.exe")
        if os.path.exists(tla_path):
            os.startfile(tla_path)
            speak("Starting Minecraft via TLauncher.")
        else:
            speak("I can't find TLauncher. Please check your installation.")
    elif cmd.startswith("play music") or cmd.startswith("play "):
        if cmd == "play music":
            m = "C:\\Users\\Public\\Music\\Sample Music\\Kalimba.mp3"
            if os.path.exists(m):
                os.startfile(m)
                speak("Playing music.")
            else:
                speak("Default music file not found.")
        else:
            song = cmd.replace("play", "").strip()
            if song:
                speak(f"Playing {song} on YouTube")
                webbrowser.open(f"https://www.youtube.com/results?search_query={song}")
            else:
                speak("Please say a song name.")
    elif cmd.startswith("search youtube for"):
        topic = cmd.replace("search youtube for", "").strip()
        if topic:
            speak(f"Searching YouTube for {topic}")
            webbrowser.open(f"https://www.youtube.com/results?search_query={topic}")
        else:
            speak("Please say what you want to search on YouTube.")
    elif cmd.startswith("pronounce "):
        word = cmd.replace("pronounce", "").strip()
        if word:
            speak(f"Pronouncing: {word}")
            speak(word)
        else:
            speak("Please say a word to pronounce.")
    elif "calculate" in cmd or "what is" in cmd:
        try:
            expr = cmd.replace("calculate", "").replace("what is", "").strip()
            expr = expr.replace("plus", "+").replace("minus", "-") \
                .replace("times", "*").replace("x", "*") \
                .replace("divided by", "/").replace("over", "/") \
                .replace("into", "*").replace("by", "/").replace("power", "**")
            allowed = {
                "sqrt": math.sqrt, "pow": math.pow, "abs": abs, "round": round,
                "sin": math.sin, "cos": math.cos, "tan": math.tan,
                "log": math.log, "pi": math.pi, "e": math.e
            }
            result = eval(expr, {"__builtins__": None}, allowed)
            try:
                speak("The answer is " + p.number_to_words(result, andword="", group=1).replace(",", ""))
            except:
                speak("The answer is " + str(result))
        except Exception:
            speak("I couldn’t solve that.")
    else:
        speak("Let me check...")
        resp = ask_gemini(cmd)
        speak(resp or "Sorry, I don't know that.")

# ================== Eyes with Black Background ===================

class EyeWidget(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.eye_width = 140
        self.eye_height = 140

        self.left_eye_base = (Window.width // 2 - 150, Window.height // 2)
        self.right_eye_base = (Window.width // 2 + 50, Window.height // 2)

        with self.canvas:
            Color(0, 0, 0, 1)
            self.bg = Rectangle(pos=(0, 0), size=Window.size)

            Color(0, 0.7, 1, 1)
            self.left_eye = RoundedRectangle(pos=self.left_eye_base, size=(self.eye_width, self.eye_height), radius=[40])
            self.right_eye = RoundedRectangle(pos=self.right_eye_base, size=(self.eye_width, self.eye_height), radius=[40])

        Clock.schedule_interval(self.animate_blink, 4)
        Window.bind(mouse_pos=self.on_mouse_move)

    def animate_blink(self, dt):
        blink_down = Animation(size=(self.eye_width, 20), duration=0.2)
        blink_up = Animation(size=(self.eye_width, self.eye_height), duration=0.2)
        (blink_down + blink_up).start(self.left_eye)
        (blink_down + blink_up).start(self.right_eye)

    def on_mouse_move(self, window, pos):
        x, y = pos
        win_width, win_height = Window.size

        offset_x = -20 if x < win_width * 0.33 else 20 if x > win_width * 0.66 else 0
        offset_y = -20 if y < win_height * 0.33 else 20 if y > win_height * 0.66 else 0

        new_left = (self.left_eye_base[0] + offset_x, self.left_eye_base[1] + offset_y)
        new_right = (self.right_eye_base[0] + offset_x, self.right_eye_base[1] + offset_y)

        Animation(pos=new_left, duration=0.2).start(self.left_eye)
        Animation(pos=new_right, duration=0.2).start(self.right_eye)

class RootLayout(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.eyes = EyeWidget()
        self.add_widget(self.eyes)
        Clock.schedule_once(lambda dt: speak("Namaste! I am Shubhavi, your smart assistant."), 1)

class ShubhaviApp(App):
    def build(self):
        Window.clearcolor = (0, 0, 0, 1)
        self.title = "Shubhavi Assistant"
        threading.Thread(target=self.input_loop, daemon=True).start()
        return RootLayout()

    def input_loop(self):
        while True:
            try:
                print("Type your command or press Enter to speak:")
                ui = input().strip()
                if ui:
                    handle_input(ui)
                else:
                    speak("Listening...")
                    voice = get_voice_input()
                    handle_input(voice)
            except Exception as e:
                print("Error in input loop:", e)

if __name__ == "__main__":
    ShubhaviApp().run()
