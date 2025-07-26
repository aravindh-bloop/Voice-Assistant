import os
import sys
import time
import datetime
import webbrowser
import wikipedia
import pyttsx3
import speech_recognition as sr
import requests
from bs4 import BeautifulSoup
import subprocess
import threading
import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox, PhotoImage
import random
from PIL import Image, ImageTk
import json
import wolframalpha
import pyautogui
import pyjokes
import pygame
from pygame import mixer
import socket
import platform
import screen_brightness_control as sbc
import speedtest

# Initialize pygame mixer
mixer.init()

class VoiceAssistant:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Voice Assistant")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        self.root.configure(bg='#2c3e50')
        
        # Initialize speech engine
        self.engine = pyttsx3.init()
        voices = self.engine.getProperty('voices')
        self.engine.setProperty('voice', voices[1].id)  # Female voice
        self.engine.setProperty('rate', 150)
        
        # Initialize recognizer
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # GUI Variables
        self.listening = False
        self.assistant_active = False
        self.wake_words = ["hey assistant", "hello assistant", "assistant", "assistant"]
        self.conversation_history = []
        
        # Load settings
        self.load_settings()
        
        # Create GUI
        self.create_gui()
        
        # Start background thread for listening
        self.listen_thread = threading.Thread(target=self.background_listen, daemon=True)
        self.listen_thread.start()
        
        # Load sounds
        self.load_sounds()
        
        # Wolfram Alpha client
        self.wolfram_client = wolframalpha.Client(self.settings.get('wolfram_alpha_app_id', ''))
        
    def load_sounds(self):
        # Try to load notification sounds
        try:
            self.start_sound = mixer.Sound('sounds/start.wav')
            self.stop_sound = mixer.Sound('sounds/stop.wav')
            self.error_sound = mixer.Sound('sounds/error.wav')
        except:
            # Create dummy sound objects if files don't exist
            class DummySound:
                def play(self): pass
            self.start_sound = DummySound()
            self.stop_sound = DummySound()
            self.error_sound = DummySound()
    
    def load_settings(self):
        # Default settings
        self.settings = {
            'wake_words': ["hey assistant", "hello assistant", "assistant"],
            'voice_speed': 150,
            'voice_gender': 'female',
            'wolfram_alpha_app_id': '',
            'news_sources': {
                'BBC': 'http://feeds.bbci.co.uk/news/rss.xml',
                'CNN': 'http://rss.cnn.com/rss/cnn_topstories.rss',
                'Reuters': 'http://feeds.reuters.com/reuters/topNews'
            },
            'app_paths': {
                'notepad': 'notepad.exe',
                'calculator': 'calc.exe',
                'chrome': 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe'
            }
        }
        
        # Try to load from file
        try:
            with open('assistant_settings.json', 'r') as f:
                self.settings.update(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    
    def save_settings(self):
        with open('assistant_settings.json', 'w') as f:
            json.dump(self.settings, f, indent=4)
    
    def create_gui(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = tk.Frame(main_frame, bg='#2c3e50')
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Logo
        try:
            logo_img = Image.open("assets/logo.png").resize((60, 60), Image.LANCZOS)
            self.logo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(header_frame, image=self.logo, bg='#2c3e50')
            logo_label.pack(side=tk.LEFT, padx=(0, 10))
        except:
            pass
        
        # Title
        title_label = tk.Label(
            header_frame, 
            text="Voice Assistant", 
            font=('Helvetica', 18, 'bold'), 
            fg='#ecf0f1', 
            bg='#2c3e50'
        )
        title_label.pack(side=tk.LEFT)
        
        # Status indicator
        self.status_var = tk.StringVar(value="Status: Sleeping")
        status_label = tk.Label(
            header_frame, 
            textvariable=self.status_var, 
            font=('Helvetica', 10), 
            fg='#bdc3c7', 
            bg='#2c3e50'
        )
        status_label.pack(side=tk.RIGHT)
        
        # Conversation area
        conv_frame = tk.LabelFrame(main_frame, text="Conversation", bg='#34495e', fg='#ecf0f1')
        conv_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.conversation_text = scrolledtext.ScrolledText(
            conv_frame, 
            wrap=tk.WORD, 
            width=60, 
            height=15, 
            font=('Helvetica', 10), 
            bg='#2c3e50', 
            fg='#ecf0f1',
            insertbackground='white'
        )
        self.conversation_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.conversation_text.config(state=tk.DISABLED)
        
        # Controls frame
        controls_frame = tk.Frame(main_frame, bg='#2c3e50')
        controls_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Listen button
        self.listen_btn = ttk.Button(
            controls_frame, 
            text="Start Listening", 
            command=self.toggle_listening,
            style='TButton'
        )
        self.listen_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Settings button
        settings_btn = ttk.Button(
            controls_frame, 
            text="Settings", 
            command=self.open_settings,
            style='TButton'
        )
        settings_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Clear button
        clear_btn = ttk.Button(
            controls_frame, 
            text="Clear", 
            command=self.clear_conversation,
            style='TButton'
        )
        clear_btn.pack(side=tk.LEFT)
        
        # Right-aligned buttons
        right_btn_frame = tk.Frame(controls_frame, bg='#2c3e50')
        right_btn_frame.pack(side=tk.RIGHT)
        
        # Help button
        help_btn = ttk.Button(
            right_btn_frame, 
            text="Help", 
            command=self.show_help,
            style='TButton'
        )
        help_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Exit button
        exit_btn = ttk.Button(
            right_btn_frame, 
            text="Exit", 
            command=self.root.quit,
            style='TButton'
        )
        exit_btn.pack(side=tk.LEFT)
        
        # Input frame
        input_frame = tk.Frame(main_frame, bg='#2c3e50')
        input_frame.pack(fill=tk.X)
        
        self.user_input = ttk.Entry(
            input_frame, 
            width=50, 
            font=('Helvetica', 10)
        )
        self.user_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.user_input.bind("<Return>", self.process_text_input)
        
        send_btn = ttk.Button(
            input_frame, 
            text="Send", 
            command=self.process_text_input,
            style='TButton'
        )
        send_btn.pack(side=tk.LEFT)
        
        # Configure styles
        self.style = ttk.Style()
        self.style.configure('TButton', font=('Helvetica', 10), background='#3498db')
        self.style.configure('TEntry', font=('Helvetica', 10))
        
        # Add some initial conversation
        self.add_to_conversation("Assistant", "Hello! I'm your voice assistant. Say 'Hey Assistant' to wake me up or type your commands.")
    
    def toggle_listening(self):
        if self.listening:
            self.listening = False
            self.listen_btn.config(text="Start Listening")
            self.status_var.set("Status: Sleeping")
            self.stop_sound.play()
        else:
            self.listening = True
            self.listen_btn.config(text="Stop Listening")
            self.status_var.set("Status: Listening...")
            self.start_sound.play()
            self.speak("I'm listening")
    
    def background_listen(self):
        while True:
            if self.listening:
                try:
                    with self.microphone as source:
                        self.recognizer.adjust_for_ambient_noise(source)
                        audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=5)
                    
                    text = self.recognizer.recognize_google(audio).lower()
                    self.add_to_conversation("You", text)
                    
                    # Check for wake word
                    if any(wake_word in text for wake_word in self.wake_words):
                        self.assistant_active = True
                        self.status_var.set("Status: Active")
                        self.start_sound.play()
                        self.speak("Yes, how can I help you?")
                        continue
                    
                    # Process command if assistant is active
                    if self.assistant_active:
                        self.process_command(text)
                    else:
                        # If no wake word, go back to listening
                        continue
                    
                except sr.WaitTimeoutError:
                    if self.assistant_active:
                        self.assistant_active = False
                        self.status_var.set("Status: Sleeping")
                        self.stop_sound.play()
                        self.speak("Going to sleep")
                except sr.UnknownValueError:
                    if self.assistant_active:
                        self.speak("I didn't catch that")
                except Exception as e:
                    print(f"Error in background_listen: {e}")
                    if self.assistant_active:
                        self.speak("Sorry, I encountered an error")
            time.sleep(0.1)
    
    def process_text_input(self, event=None):
        text = self.user_input.get()
        if text.strip():
            self.add_to_conversation("You", text)
            self.user_input.delete(0, tk.END)
            
            # Check for wake word in text input
            if any(wake_word in text.lower() for wake_word in self.wake_words):
                self.assistant_active = True
                self.status_var.set("Status: Active")
                self.start_sound.play()
                self.speak("Yes, how can I help you?")
            elif self.assistant_active:
                self.process_command(text)
            else:
                self.add_to_conversation("Assistant", "Say 'Hey Assistant' to wake me up first.")
    
    def process_command(self, command):
        try:
            command = command.lower()
            
            # Basic greetings
            if any(word in command for word in ["hello", "hi", "hey"]):
                responses = ["Hello!", "Hi there!", "Hey, how can I help?"]
                response = random.choice(responses)
                self.speak(response)
                return
            
            # Goodbye
            elif any(word in command for word in ["bye", "goodbye", "see you"]):
                self.speak("Goodbye! Have a nice day.")
                self.assistant_active = False
                self.status_var.set("Status: Sleeping")
                self.stop_sound.play()
                return
            
            # Time
            elif "time" in command:
                current_time = datetime.datetime.now().strftime("%I:%M %p")
                self.speak(f"The current time is {current_time}")
                return
            
            # Date
            elif "date" in command:
                current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
                self.speak(f"Today is {current_date}")
                return
            
            # Open YouTube
            elif "youtube" in command:
                self.speak("Opening YouTube")
                webbrowser.open("https://www.youtube.com")
                return
            
            # Open Google
            elif "google" in command:
                self.speak("Opening Google")
                webbrowser.open("https://www.google.com")
                return
            
            # Search the web
            elif "search" in command and "for" in command:
                query = command.split("for")[1].strip()
                self.speak(f"Searching the web for {query}")
                webbrowser.open(f"https://www.google.com/search?q={query}")
                return
            
            # Search Wikipedia
            elif "wikipedia" in command or "wiki" in command:
                query = command.replace("wikipedia", "").replace("wiki", "").strip()
                if not query:
                    self.speak("What would you like me to search on Wikipedia?")
                    return
                
                try:
                    self.speak(f"Searching Wikipedia for {query}")
                    result = wikipedia.summary(query, sentences=2)
                    self.speak("According to Wikipedia")
                    self.speak(result)
                except wikipedia.exceptions.DisambiguationError as e:
                    self.speak(f"There are multiple results for {query}. Can you be more specific?")
                except wikipedia.exceptions.PageError:
                    self.speak(f"Sorry, I couldn't find any information about {query} on Wikipedia.")
                return
            
            # Read news
            elif "news" in command:
                self.read_news()
                return
            
            # Open applications
            elif "open" in command:
                app = command.replace("open", "").strip()
                self.open_application(app)
                return
            
            # Tell a joke
            elif "joke" in command:
                joke = pyjokes.get_joke()
                self.speak(joke)
                return
            
            # System information
            elif "system" in command and "info" in command:
                self.get_system_info()
                return
            
            # Weather
            elif "weather" in command:
                location = command.replace("weather", "").replace("in", "").strip()
                if not location:
                    self.speak("Which location's weather would you like to know?")
                    return
                self.get_weather(location)
                return
            
            # Calculate
            elif "calculate" in command or "what is" in command and ("+" in command or "-" in command or "*" in command or "/" in command):
                self.calculate(command)
                return
            
            # Set brightness
            elif "brightness" in command and ("set" in command or "change" in command):
                self.set_brightness(command)
                return
            
            # Internet speed test
            elif "speed test" in command or "internet speed" in command:
                self.run_speed_test()
                return
            
            # Wolfram Alpha questions
            elif "what is" in command or "who is" in command or "where is" in command or "how many" in command:
                try:
                    res = self.wolfram_client.query(command)
                    answer = next(res.results).text
                    self.speak(answer)
                except:
                    self.speak("Sorry, I couldn't find an answer to that question.")
                return
            
            # If no command matches
            self.speak("I'm not sure how to help with that. Can you try something else?")
        
        except Exception as e:
            print(f"Error in process_command: {e}")
            self.error_sound.play()
            self.speak("Sorry, I encountered an error processing that command.")
    
    def speak(self, text):
        self.add_to_conversation("Assistant", text)
        self.engine.say(text)
        self.engine.runAndWait()
    
    def add_to_conversation(self, speaker, text):
        self.conversation_text.config(state=tk.NORMAL)
        self.conversation_text.insert(tk.END, f"{speaker}: {text}\n\n")
        self.conversation_text.config(state=tk.DISABLED)
        self.conversation_text.see(tk.END)
        self.conversation_history.append((speaker, text))
    
    def clear_conversation(self):
        self.conversation_text.config(state=tk.NORMAL)
        self.conversation_text.delete(1.0, tk.END)
        self.conversation_text.config(state=tk.DISABLED)
        self.conversation_history = []
        self.add_to_conversation("Assistant", "Conversation cleared.")
    
    def read_news(self):
        try:
            self.speak("Fetching the latest news headlines")
            
            # Select a random news source
            source, url = random.choice(list(self.settings['news_sources'].items()))
            
            # Fetch RSS feed
            response = requests.get(url)
            soup = BeautifulSoup(response.content, features='xml')
            items = soup.findAll('item')[:5]  # Get top 5 news items
            
            self.speak(f"Here are the latest headlines from {source}")
            
            for i, item in enumerate(items):
                title = item.title.text
                self.speak(f"Headline {i+1}: {title}")
                time.sleep(1)  # Pause between headlines
            
            self.speak("That's all for now. Would you like me to read more?")
        
        except Exception as e:
            print(f"Error in read_news: {e}")
            self.speak("Sorry, I couldn't fetch the news at the moment.")
    
    def open_application(self, app_name):
        app_name = app_name.lower()
        app_mapping = {
            'notepad': 'notepad.exe',
            'calculator': 'calc.exe',
            'chrome': 'chrome.exe',
            'word': 'winword.exe',
            'excel': 'excel.exe',
            'powerpoint': 'powerpnt.exe',
            'paint': 'mspaint.exe',
            'vlc': 'vlc.exe',
            'spotify': 'spotify.exe'
        }
        
        # Check custom paths first
        if app_name in self.settings['app_paths']:
            try:
                os.startfile(self.settings['app_paths'][app_name])
                self.speak(f"Opening {app_name}")
                return
            except Exception as e:
                print(f"Error opening {app_name}: {e}")
        
        # Check default mappings
        if app_name in app_mapping:
            try:
                os.startfile(app_mapping[app_name])
                self.speak(f"Opening {app_name}")
                return
            except Exception as e:
                print(f"Error opening {app_name}: {e}")
        
        # Try to find the application
        try:
            subprocess.Popen(app_name, shell=True)
            self.speak(f"Opening {app_name}")
        except Exception as e:
            print(f"Error opening {app_name}: {e}")
            self.speak(f"Sorry, I couldn't open {app_name}")
    
    def get_system_info(self):
        try:
            self.speak("Getting system information")
            
            info = {
                "System": platform.system(),
                "Node Name": platform.node(),
                "Release": platform.release(),
                "Version": platform.version(),
                "Machine": platform.machine(),
                "Processor": platform.processor(),
                "IP Address": socket.gethostbyname(socket.gethostname())
            }
            
            response = "Here's your system information:\n"
            for key, value in info.items():
                response += f"{key}: {value}\n"
                self.add_to_conversation("System", f"{key}: {value}")
            
            self.speak("I've displayed the system information in our conversation window.")
        
        except Exception as e:
            print(f"Error in get_system_info: {e}")
            self.speak("Sorry, I couldn't retrieve the system information.")
    
    def get_weather(self, location):
        try:
            self.speak(f"Getting weather information for {location}")
            
            # Using OpenWeatherMap API (you would need an API key)
            api_key = "your_api_key_here"  # Replace with actual API key
            base_url = "http://api.openweathermap.org/data/2.5/weather?"
            complete_url = f"{base_url}appid={api_key}&q={location}"
            
            response = requests.get(complete_url)
            data = response.json()
            
            if data["cod"] != "404":
                main = data["main"]
                temperature = main["temp"] - 273.15  # Convert from Kelvin to Celsius
                pressure = main["pressure"]
                humidity = main["humidity"]
                weather_desc = data["weather"][0]["description"]
                
                weather_info = (
                    f"Current temperature is {temperature:.1f} degrees Celsius\n"
                    f"Atmospheric pressure is {pressure} hPa\n"
                    f"Humidity is {humidity}%\n"
                    f"Weather description: {weather_desc}"
                )
                
                self.speak(f"Here's the weather for {location}")
                self.add_to_conversation("Weather", weather_info)
                self.speak(weather_info)
            else:
                self.speak(f"Sorry, I couldn't find weather information for {location}")
        
        except Exception as e:
            print(f"Error in get_weather: {e}")
            self.speak("Sorry, I couldn't fetch the weather information at the moment.")
    
    def calculate(self, command):
        try:
            # Extract the mathematical expression
            if "calculate" in command:
                expr = command.split("calculate")[1].strip()
            elif "what is" in command:
                expr = command.split("what is")[1].strip()
            
            # Replace words with operators
            expr = (expr.replace("plus", "+")
                      .replace("minus", "-")
                      .replace("times", "*")
                      .replace("multiplied by", "*")
                      .replace("divided by", "/")
                      .replace("over", "/"))
            
            # Remove question marks and other non-math characters
            expr = ''.join(c for c in expr if c in '0123456789+-*/.() ')
            
            # Evaluate the expression
            result = eval(expr)
            
            self.speak(f"The result is {result}")
            self.add_to_conversation("Calculator", f"{expr} = {result}")
        
        except Exception as e:
            print(f"Error in calculate: {e}")
            self.speak("Sorry, I couldn't perform that calculation.")
    
    def set_brightness(self, command):
        try:
            # Extract percentage
            percent = None
            words = command.split()
            for word in words:
                if word.endswith('%'):
                    percent = int(word[:-1])
                    break
            
            if percent is None:
                self.speak("Please specify a percentage for brightness")
                return
            
            # Set brightness
            sbc.set_brightness(percent)
            self.speak(f"Screen brightness set to {percent}%")
        
        except Exception as e:
            print(f"Error in set_brightness: {e}")
            self.speak("Sorry, I couldn't adjust the brightness.")
    
    def run_speed_test(self):
        try:
            self.speak("Running internet speed test. This may take a moment...")
            
            st = speedtest.Speedtest()
            st.get_best_server()
            
            download_speed = st.download() / 1_000_000  # Convert to Mbps
            upload_speed = st.upload() / 1_000_000  # Convert to Mbps
            
            result = (
                f"Download speed: {download_speed:.2f} Mbps\n"
                f"Upload speed: {upload_speed:.2f} Mbps"
            )
            
            self.speak("Here are your internet speed test results")
            self.add_to_conversation("Speed Test", result)
            self.speak(f"Download speed is {download_speed:.2f} megabits per second")
            self.speak(f"Upload speed is {upload_speed:.2f} megabits per second")
        
        except Exception as e:
            print(f"Error in run_speed_test: {e}")
            self.speak("Sorry, I couldn't complete the speed test.")
    
    def open_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Assistant Settings")
        settings_window.geometry("500x400")
        settings_window.resizable(False, False)
        
        # Wake words frame
        wake_frame = ttk.LabelFrame(settings_window, text="Wake Words")
        wake_frame.pack(fill=tk.X, padx=10, pady=5)
        
        wake_label = ttk.Label(wake_frame, text="Current wake words:")
        wake_label.pack(anchor=tk.W, padx=5, pady=2)
        
        self.wake_words_entry = ttk.Entry(wake_frame, width=50)
        self.wake_words_entry.pack(fill=tk.X, padx=5, pady=5)
        self.wake_words_entry.insert(0, ", ".join(self.settings['wake_words']))
        
        # Voice settings frame
        voice_frame = ttk.LabelFrame(settings_window, text="Voice Settings")
        voice_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(voice_frame, text="Voice Speed:").pack(anchor=tk.W, padx=5, pady=2)
        self.voice_speed = tk.IntVar(value=self.settings['voice_speed'])
        speed_slider = ttk.Scale(
            voice_frame, 
            from_=100, 
            to=200, 
            orient=tk.HORIZONTAL, 
            variable=self.voice_speed,
            command=lambda v: self.engine.setProperty('rate', int(float(v)))
        )
        speed_slider.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(voice_frame, text="Voice Gender:").pack(anchor=tk.W, padx=5, pady=2)
        self.voice_gender = tk.StringVar(value=self.settings['voice_gender'])
        male_radio = ttk.Radiobutton(
            voice_frame, 
            text="Male", 
            variable=self.voice_gender, 
            value='male',
            command=self.update_voice_gender
        )
        male_radio.pack(anchor=tk.W, padx=5, pady=2)
        
        female_radio = ttk.Radiobutton(
            voice_frame, 
            text="Female", 
            variable=self.voice_gender, 
            value='female',
            command=self.update_voice_gender
        )
        female_radio.pack(anchor=tk.W, padx=5, pady=2)
        
        # Application paths frame
        app_frame = ttk.LabelFrame(settings_window, text="Application Paths")
        app_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.app_path_vars = {}
        for i, (app, path) in enumerate(self.settings['app_paths'].items()):
            frame = ttk.Frame(app_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
            
            ttk.Label(frame, text=f"{app.capitalize()}:").pack(side=tk.LEFT, padx=(0, 5))
            
            var = tk.StringVar(value=path)
            self.app_path_vars[app] = var
            
            entry = ttk.Entry(frame, textvariable=var, width=40)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            browse_btn = ttk.Button(frame, text="Browse", command=lambda a=app: self.browse_app_path(a))
            browse_btn.pack(side=tk.LEFT, padx=(5, 0))
        
        # Buttons frame
        btn_frame = ttk.Frame(settings_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        save_btn = ttk.Button(btn_frame, text="Save", command=self.save_settings_changes)
        save_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        cancel_btn = ttk.Button(btn_frame, text="Cancel", command=settings_window.destroy)
        cancel_btn.pack(side=tk.LEFT)
    
    def update_voice_gender(self):
        voices = self.engine.getProperty('voices')
        if self.voice_gender.get() == 'male':
            self.engine.setProperty('voice', voices[0].id)
        else:
            self.engine.setProperty('voice', voices[1].id)
    
    def browse_app_path(self, app):
        initial_dir = os.path.dirname(self.app_path_vars[app].get()) or "C:\\"
        file_path = filedialog.askopenfilename(
            initialdir=initial_dir,
            title=f"Select {app} executable",
            filetypes=(("Executable files", "*.exe"), ("All files", "*.*"))
        )
        if file_path:
            self.app_path_vars[app].set(file_path)
    
    def save_settings_changes(self):
        # Update wake words
        new_wake_words = [w.strip() for w in self.wake_words_entry.get().split(",") if w.strip()]
        if new_wake_words:
            self.settings['wake_words'] = new_wake_words
            self.wake_words = new_wake_words
        
        # Update voice settings
        self.settings['voice_speed'] = self.voice_speed.get()
        self.settings['voice_gender'] = self.voice_gender.get()
        self.engine.setProperty('rate', self.voice_speed.get())
        self.update_voice_gender()
        
        # Update app paths
        for app, var in self.app_path_vars.items():
            self.settings['app_paths'][app] = var.get()
        
        # Save to file
        self.save_settings()
        
        # Close settings window
        self.root.focus_set()
        for window in self.root.winfo_children():
            if isinstance(window, tk.Toplevel) and window.title() == "Assistant Settings":
                window.destroy()
                break
        
        self.speak("Settings have been updated")
    
    def show_help(self):
        help_text = """Voice Assistant Help Guide

Basic Commands:
- "Hey Assistant" or "Hello Assistant" - Wake up the assistant
- "What's the time?" - Get current time
- "What's today's date?" - Get current date
- "Open [application]" - Open an application
- "Search for [query]" - Search the web
- "Wikipedia [topic]" - Search Wikipedia
- "Tell me a joke" - Hear a random joke
- "Read the news" - Get news headlines
- "Goodbye" - Put assistant to sleep

Advanced Features:
- "What is [question]?" - Answer factual questions
- "Calculate [expression]" - Perform calculations
- "Set brightness to X%" - Adjust screen brightness
- "Run speed test" - Check internet speed
- "System information" - Get PC specs

You can also type commands in the input box below."""
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Assistant Help")
        help_window.geometry("600x500")
        
        text = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, width=70, height=30)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(tk.INSERT, help_text)
        text.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    assistant = VoiceAssistant(root)
    root.mainloop()