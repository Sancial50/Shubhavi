import os, webbrowser, pyttsx3, openai, wikipedia, math, ctypes, threading, csv, inflect
import speech_recognition as sr
from datetime import datetime
from dotenv import load_dotenv

# === FULLSCREEN WITHOUT RESOLUTION CHANGE ===
from kivy.config import Config
Config.set('graphics', 'borderless', '1')
Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'width', '1920')
Config.set('graphics', 'height', '1080')

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Line, Rectangle
from kivy.core.window import Window
from kivy.uix.widget import Widget

# === SET WINDOW SETTINGS ===
Window.size = (1920, 1080)
Window.top = 0
Window.left = 0
Window.borderless = True

# === LOAD ENV, SETUP ENGINES ===
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
engine = pyttsx3.init()
engine.setProperty('rate', 160)
engine.setProperty('volume', 1.0)
recognizer = sr.Recognizer()
muted = False
speech_thread = None
p = inflect.engine()

# === LOAD QA CSV FILE ===
qa_data = {}
try:
    with open("qa_data.csv", newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            if len(row) >= 2:
                q, a = row[0].strip().lower(), row[1].strip()
                qa_data[q] = a
except:
    pass

# === SPEAK FUNCTION ===
def speak(text):
    global speech_thread
    def run():
        if not muted:
            print(f"\nShubhavi: {text}\n")
            engine.say(text)
            engine.runAndWait()
    if speech_thread and speech_thread.is_alive():
        engine.stop()
    speech_thread = threading.Thread(target=run)
    speech_thread.start()

# === GET VOICE INPUT ===
def get_voice_input():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    try:
        text = recognizer.recognize_google(audio).lower()
        print(f"You (Voice): {text}")
        return text
    except:
        speak("Sorry, I didn't catch that.")
        return ""

# === OPENAI FALLBACK ===
def ask_openai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error: {e}"

# === MAIN COMMAND HANDLER ===
def handle_input(cmd):
    global muted
    cmd = cmd.strip().lower()
    if not cmd:
        return

    if cmd in qa_data:
        speak(qa_data[cmd])
        return

    if cmd in ["who is your inventor"]:
        speak("Aradhya is my boss.")
    elif cmd in ["exit", "bye", "shutdown yourself", "close yourself"]:
        speak("Shutting myself down.")
        os._exit(0)
    elif cmd in ["hi", "hello", "hey"]:
        speak("Namaste! How can I help you?")
    elif cmd in ["how are you"]:
        speak("I'm great and ready to assist!")
    elif cmd in ["what is your name", "who are you"]:
        speak("I am Shubhavi, your smart assistant.")
    elif cmd == "mute":
        muted = True
    elif cmd == "unmute":
        muted = False
    elif "time" in cmd:
        speak("The time is " + datetime.now().strftime("%I:%M %p"))
    elif "date" in cmd:
        try:
            speak("Today is " + datetime.now().strftime("%A, %d %B %Y"))
        except Exception as e:
            print("Date error:", e)
            speak("Sorry, I couldn't fetch the date.")
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
        except Exception as e:
            print("Lock error:", e)
            speak("Unable to lock the PC.")
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
        vlc_path = "C:\\Program Files\\VideoLAN\\VLC\\vlc.exe"
        if os.path.exists(vlc_path):
            os.startfile(vlc_path)
            speak("Opening VLC")
        else:
            speak("VLC is not installed.")
    elif "open chrome" in cmd:
        chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        if os.path.exists(chrome_path):
            os.startfile(chrome_path)
            speak("Opening Chrome")
        else:
            speak("Chrome is not installed.")
    elif "search wikipedia for" in cmd:
        topic = cmd.replace("search wikipedia for", "").strip()
        try:
            summary = wikipedia.summary(topic, sentences=2)
            speak(summary)
        except:
            speak("Sorry, I couldn't find that on Wikipedia.")
    elif "play music" in cmd or cmd.startswith("play "):
        if cmd.strip() == "play music":
            music_path = "C:\\Users\\Public\\Music\\Sample Music\\Kalimba.mp3"
            if os.path.exists(music_path):
                os.startfile(music_path)
                speak("Playing music.")
            else:
                speak("Default music file not found. Please say a song name to play on YouTube.")
        else:
            song = cmd.replace("play", "").replace("music", "").strip()
            if song:
                speak(f"Playing {song} on YouTube")
                webbrowser.open(f"https://www.youtube.com/results?search_query={song}")
            else:
                speak("Please say a song name.")
    elif "search youtube for" in cmd:
        topic = cmd.replace("search youtube for", "").strip()
        if topic:
            speak(f"Searching YouTube for {topic}")
            webbrowser.open(f"https://www.youtube.com/results?search_query={topic}")
        else:
            speak("Please say what you want to search on YouTube.")
    elif "calculate" in cmd or "what is" in cmd:
        try:
            expr = cmd.replace("calculate", "").replace("what is", "").strip()
            expr = expr.replace("plus", "+").replace("minus", "-").replace("times", "*")\
                       .replace("x", "*").replace("divided by", "/").replace("over", "/")\
                       .replace("into", "*").replace("by", "/").replace("power", "**")
            allowed = {"sqrt": math.sqrt, "pow": math.pow, "abs": abs, "round": round,
                       "sin": math.sin, "cos": math.cos, "tan": math.tan,
                       "log": math.log, "pi": math.pi, "e": math.e}
            result = eval(expr, {"__builtins__": None}, allowed)
            try:
                readable = p.number_to_words(result, andword="", group=1).replace(",", "")
                speak(f"The answer is {readable}")
            except:
                speak(f"The answer is {result}")
        except Exception as e:
            speak("I couldn't solve that.")
            print(f"Math error: {e}")
    else:
        speak("Let me check...")
        response = ask_openai(cmd)
        speak(response if response else "Sorry, I don't know that.")

# === SOUND WAVE ANIMATION ===
class SoundWave(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_interval(self.animate, 1 / 30)
        self.radius = 320
        self.growing = True

    def animate(self, dt):
        center_x = Window.width / 2
        center_y = Window.height / 2
        self.canvas.clear()
        with self.canvas:
            Color(0.2, 0.6, 1, 0.4)
            Line(circle=(center_x, center_y, 300), width=2)
            Color(0.2, 0.6, 1, 0.2)
            Line(circle=(center_x, center_y, self.radius), width=1.5)
        if self.growing:
            self.radius += 5
            if self.radius > 360:
                self.growing = False
        else:
            self.radius -= 5
            if self.radius < 320:
                self.growing = True

# === MAIN LAYOUT ===
class RootLayout(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0, 0.1, 0.3, 1)
            self.bg = Rectangle(size=Window.size, pos=(0, 0))
        self.wave = SoundWave()
        self.add_widget(self.wave)
        Clock.schedule_once(lambda dt: speak("Namaste! I am Shubhavi, your smart assistant."), 1)

# === MAIN APP ===
class ShubhaviApp(App):
    def build(self):
        Window.clearcolor = (0, 0, 0, 1)
        self.title = "Shubhavi Assistant"
        Clock.schedule_interval(lambda dt: None, 1)  # Keep Kivy alive
        threading.Thread(target=self.input_loop, daemon=True).start()
        return RootLayout()

    def input_loop(self):
        while True:
            try:
                print("Type your command or press Enter to speak:")
                user_input = input().strip()
                if user_input:
                    handle_input(user_input)
                else:
                    speak("Listening...")
                    voice = get_voice_input()
                    handle_input(voice)
            except Exception as e:
                print("Error in input loop:", e)

# === RUN ===
if __name__ == "__main__":
    try:
        print("Starting Shubhavi Assistant...")
        ShubhaviApp().run()
    except Exception as e:
        print("App crashed with error:", e)
        import traceback
        traceback.print_exc()
