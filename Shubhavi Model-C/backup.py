import os
import webbrowser
import openai
import wikipedia
import math
import ctypes
import threading
import csv
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
from kivy.uix.image import Image
from queue import Queue

# Window setup
Window.size = (1920, 1080)
Window.top = 0
Window.left = 0
Window.borderless = True

# Load .env and APIs
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
recognizer = sr.Recognizer()
muted = False
p = inflect.engine()

# Load CSV QA
qa_data = {}
try:
    with open("qa_data.csv", encoding="utf-8", newline="") as f:
        for row in csv.reader(f):
            if len(row) >= 2:
                qa_data[row[0].strip().lower()] = row[1].strip()
except Exception as e:
    print("QA load failed:", e)

# Speech Queue
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
        print(f"\nShubhavi: {text}\n")
        speech_queue.put(text)

def get_voice_input():
    with sr.Microphone() as src:
        recognizer.adjust_for_ambient_noise(src)
        audio = recognizer.listen(src)
    try:
        text = recognizer.recognize_google(audio).lower()
        print(f"You (Voice): {text}")
        return text
    except:
        speak("Sorry, I didn’t catch that.")
        return ""

def ask_openai(prompt):
    try:
        resp = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

def handle_input(cmd):
    # Custom logic or OpenAI fallback
    cmd = cmd.strip().lower()
    if not cmd:
        return

    if cmd in qa_data:
        speak(qa_data[cmd])
    elif "open youtube" in cmd:
        webbrowser.open("https://youtube.com")
    elif "open google" in cmd:
        webbrowser.open("https://google.com")
    else:
        response = ask_openai(cmd)
        speak(response)

# ======================= EYE WIDGET ===========================

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

        # Eyelashes (your image)
        self.left_lash = Image(source='eyelash.png', size_hint=(None, None), size=(160, 100), pos=(self.left_eye_base[0] - 10, self.left_eye_base[1] + 100))
        self.right_lash = Image(source='eyelash.png', size_hint=(None, None), size=(160, 100), pos=(self.right_eye_base[0] - 10, self.right_eye_base[1] + 100))
        self.add_widget(self.left_lash)
        self.add_widget(self.right_lash)

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

        Animation(pos=new_left, duration=0.1).start(self.left_eye)
        Animation(pos=new_right, duration=0.1).start(self.right_eye)

        self.left_lash.pos = (new_left[0] - 10, new_left[1] + 100)
        self.right_lash.pos = (new_right[0] - 10, new_right[1] + 100)

        # Eye Grow logic
        if x < win_width * 0.33:
            Animation(size=(self.eye_width + 20, self.eye_height + 20), duration=0.1).start(self.left_eye)
            Animation(size=(self.eye_width, self.eye_height), duration=0.1).start(self.right_eye)
        elif x > win_width * 0.66:
            Animation(size=(self.eye_width, self.eye_height), duration=0.1).start(self.left_eye)
            Animation(size=(self.eye_width + 20, self.eye_height + 20), duration=0.1).start(self.right_eye)
        else:
            Animation(size=(self.eye_width, self.eye_height), duration=0.1).start(self.left_eye)
            Animation(size=(self.eye_width, self.eye_height), duration=0.1).start(self.right_eye)

# =================== KIVY APP =====================

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
