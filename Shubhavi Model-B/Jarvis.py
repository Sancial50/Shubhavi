import speech_recognition as sr
import pyttsx3
import requests
import json
import re
import webbrowser
import os
import subprocess
import time
import threading
import tempfile
import queue
from gtts import gTTS
import playsound
from tkinter import Tk, Label
from PIL import Image, ImageTk, ImageSequence

# === CONFIGURATION ===
DEEPSEEK_API_KEY = "your_deepseek_api_key"
SERP_API_KEY = "your_serp_api_key"
DEEPSEEK_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Initialize TTS engine
engine = pyttsx3.init('sapi5')
engine.setProperty("rate", 180)

# Initialize speech recognizer
recognizer = sr.Recognizer()
interrupt_event = threading.Event()
command_queue = queue.Queue()

# === Show GIF animation function ===
def show_gif_animation(gif_path):
    def start_animation():
        def update_frame(counter):
            try:
                frame = frames[counter]
                gif_label.configure(image=frame)
                window.after(100, update_frame, (counter + 1) % len(frames))
            except Exception as e:
                print("❌ Frame update error:", e)

        global window, gif_label, frames
        window = Tk()
        window.title("Jarvis AI")
        window.configure(bg="black")
        window.geometry("500x500+600+200")
        window.overrideredirect(True)

        gif = Image.open(gif_path)
        frames = [ImageTk.PhotoImage(frame.copy().convert("RGBA")) for frame in ImageSequence.Iterator(gif)]

        gif_label = Label(window, bg="black")
        gif_label.pack(expand=True)

        update_frame(0)
        window.mainloop()

    threading.Thread(target=start_animation, daemon=True).start()

# Text input thread
def text_input_thread():
    while True:
        try:
            user_input = input("💬 Type your command (or type 'exit'): ").strip()
            if user_input:
                command_queue.put(user_input)
        except Exception as e:
            print("Text input error:", e)

# Background listener thread for interruption
def persistent_interruption_listener():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        while True:
            try:
                print("🎧 Listening for 'Jarvis stop' command...")
                audio = recognizer.listen(source, timeout=2, phrase_time_limit=3)
                said = recognizer.recognize_google(audio)
                print("🔈 Interruption Listener Heard:", said)
                if "jarvis stop" in said.lower():
                    interrupt_event.set()
                    engine.stop()
                    print("🛑 Interruption triggered.")
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except Exception as e:
                print("🎧 Listener Error:", e)

listener_thread = threading.Thread(target=persistent_interruption_listener, daemon=True)
listener_thread.start()

# Speak Function
def speak(text, lang="en", allow_interruption=True):
    interrupt_event.clear()
    print("🗣 Speaking:", text)

    if lang == "hi":
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                temp_path = fp.name
            tts = gTTS(text=text, lang='hi')
            tts.save(temp_path)
            playsound.playsound(temp_path)
            os.remove(temp_path)
        except Exception as e:
            print("Error in Hindi TTS:", e)
    else:
        if not allow_interruption:
            engine.say(text)
            engine.runAndWait()
            return
        words = text.split()
        chunk = ""
        for word in words:
            if interrupt_event.is_set():
                print("🛑 Speech manually interrupted.")
                break
            chunk += word + " "
            if len(chunk) > 100 or word == words[-1]:
                engine.say(chunk)
                engine.runAndWait()
                chunk = ""

def listen():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print("🎤 Listening...")
        audio = recognizer.listen(source)
    try:
        print("🔍 Recognizing...")
        query = recognizer.recognize_google(audio)
        print("You said:", query)
        return query
    except Exception:
        return None

def clean_response(text):
    text = re.sub(r'\\n', ' ', text)
    text = re.sub(r'\n', ' ', text)
    text = re.sub(r'\r', '', text)
    text = re.sub(r'[*_`#>\[\]{}|]', '', text)
    text = re.sub(r'\\boxed', '', text)
    text = re.sub(r'\\frac', '', text)
    text = re.sub(r'\\sqrt', '', text)
    text = re.sub(r'\\textbf', '', text)
    text = re.sub(r'\\begin{[^}]+}', '', text)
    text = re.sub(r'\\end{[^}]+}', '', text)
    text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', text)
    text = re.sub(r'\s{2,}', ' ', text)
    return text.strip()

def google_search(query):
    print(f"🔎 Performing Google search for: {query}")
    params = {
        "engine": "google",
        "q": query,
        "api_key": SERP_API_KEY,
        "num": 3
    }
    try:
        response = requests.get("https://serpapi.com/search", params=params, timeout=5)
        data = response.json()
        snippets = []
        if "organic_results" in data:
            for result in data["organic_results"][:3]:
                if "snippet" in result:
                    snippets.append(result["snippet"])
        print("🔎 Snippets Found:")
        for snippet in snippets:
            print("-", snippet)
        return snippets
    except Exception as e:
        print(f"❌ Google Search Error: {e}")
        return []

def chat_with_deepseek(prompt):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://your-site-or-project.com",
        "X-Title": "Jarvis Assistant"
    }
    data = {
        "model": "deepseek/deepseek-r1-zero:free",
        "messages": [
            {"role": "system", "content": "You are Jarvis, a helpful voice assistant."},
            {"role": "user", "content": f"Context: {prompt['context']}\n\nQuestion: {prompt['question']}"}
        ]
    }
    try:
        response = requests.post(DEEPSEEK_API_URL, headers=headers, data=json.dumps(data), timeout=10)
        if response.status_code == 200:
            result = response.json()
            answer = result["choices"][0]["message"]["content"]
            print("🧠 AI Response:", answer)
            return clean_response(answer)
        else:
            print(f"❌ Deepseek Error: {response.status_code} {response.text}")
            return "Sorry, I couldn't get a response from the AI."
    except Exception as e:
        print(f"❌ Exception in Deepseek: {e}")
        return "There was a problem connecting to the AI."

def rag_response(user_question):
    snippets = google_search(user_question)
    context = " ".join(snippets) if snippets else "No recent information found."
    prompt = {
        "context": context,
        "question": user_question
    }
    return chat_with_deepseek(prompt)

def detect_language(text):
    for ch in text:
        if '\u0900' <= ch <= '\u097F':
            return "hi"
    return "en"

# === MAIN ===
def main():
    show_gif_animation("C:\\Users\\gaura\\Desktop\\Phucological article\\AI Animation.gif")
    threading.Thread(target=text_input_thread, daemon=True).start()
    speak("Hello, I am Jarvis. Say 'Jarvis' or type to activate me.")

    while True:
        print("🕒 Waiting for 'Jarvis' (voice or typed)...")
        wake_input = listen()

        if not wake_input and not command_queue.empty():
            wake_input = command_queue.get()

        if wake_input and "jarvis" in wake_input.lower():
            speak("Yes? What would you like me to do?")
            command = listen()

            if not command and not command_queue.empty():
                command = command_queue.get()

            if not command:
                speak("Sorry, I didn't catch that.")
                continue

            command_lower = command.lower()

            if any(word in command_lower for word in ["exit", "quit", "stop", "bye"]):
                speak("Goodbye! Have a great day.")
                break

            elif "shutdown" in command_lower:
                speak("Shutting down the system.")
                os.system("shutdown /s /t 1")
                break

            elif "open chrome" in command_lower:
                speak("Opening Chrome.")
                chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
                subprocess.Popen([chrome_path])

            elif "search for" in command_lower or "google" in command_lower:
                search_query = command_lower.replace("search for", "").replace("google", "").strip()
                if not search_query:
                    speak("What should I search for?")
                    search_query = listen()
                    if not search_query and not command_queue.empty():
                        search_query = command_queue.get()
                    if not search_query:
                        speak("Sorry, no search query detected.")
                        continue
                speak("Searching, please wait...")
                start = time.time()
                answer = rag_response(search_query)
                end = time.time()
                print(f"⏱ RAG time: {end - start:.2f}s")
                lang = detect_language(answer)
                speak(answer, lang=lang)

            elif "open folder" in command_lower:
                folder = command_lower.replace("open folder", "").strip()
                folder_path = os.path.join("C:\\Users\\YourUsername\\", folder)
                if os.path.exists(folder_path):
                    speak(f"Opening folder {folder}")
                    os.startfile(folder_path)
                else:
                    speak("Sorry, I can't find that folder.")

            else:
                speak("Let me check, please wait...")
                start = time.time()
                answer = rag_response(command)
                end = time.time()
                print(f"⏱ RAG time: {end - start:.2f}s")
                lang = detect_language(answer)
                speak(answer, lang=lang)

if __name__ == "__main__":
    main()
