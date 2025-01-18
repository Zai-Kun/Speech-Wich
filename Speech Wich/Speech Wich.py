from threading import Thread
import tkinter
import time
import os, platform, subprocess
import configparser

from pathvalidate import sanitize_filename
import customtkinter

from btts import Bing
from windows.locale_selection_window import localeSelectionWindow

bing = Bing()
bing.initialize_environment()


class SpeechWich(customtkinter.CTk):
    CONFIG_FILE_PATH = 'data/config.ini'

    AUDIO_METHODS = {
        "Windows": "data/mpg123/mpg123.exe",
        "Linux": "mpg123",
        "Darwin": "afplay",
        "Other": "pygame",
    }
    
    COMPACT_MODE_SETTINGS = {
        "info_label": {"row": 0, "column": 0, "pady": 0, "sticky": "n"},
        "speed_slider": {"row": 1, "column": 0, "padx": 30, "pady": 0, "sticky": "w"},
        "speed_value_indicator": {"row": 1, "column": 0, "padx": 30, "pady": 0, "sticky": "e"},
        "filename_entry": {"row": 2, "column": 0, "padx": 30, "pady": (10, 0), "sticky": "ew"},
        "combobox_voices": {"row": 3, "column": 0, "padx": 30, "pady": (10, 0), "sticky": "ew"},
        "select_locale_button": {"row": 4, "column": 0, "padx": 30, "pady": (10, 0), "sticky": "ew"},
        "input_textbox": {"row": 5, "column": 0, "padx": 30, "pady": (10, 0), "sticky": "ew"},
        "ctts_and_save": {"row": 6, "column": 0, "padx": 30, "pady": (30, 0), "sticky": "ew"},
        "play_converted_speech_button": {"row": 7, "column": 0, "padx": 30, "pady": (17, 0), "sticky": "ew"},
    }

    DEFAULT_MODE_SETTINGS = {
        "info_label": {"row": 0, "column": 0, "padx": 30, "pady": 0, "sticky": "e"},
        "speed_slider": {"row": 0, "column": 0, "padx": 30, "pady": 0, "sticky": "w"},
        "speed_value_indicator": {"row": 0, "column": 0, "padx": 140, "pady": 0, "sticky": "w"},
        "filename_entry": {"row": 1, "column": 0, "padx": (30, 0), "pady": 0, "sticky": "w"},
        "select_locale_button": {"row": 1, "column": 0, "padx": (0, 200), "pady": 0, "sticky": "e"},
        "combobox_voices": {"row": 1, "column": 0, "padx": (0, 30), "pady": 0, "sticky": "e"},
        "input_textbox": {"row": 2, "column": 0, "padx": 30, "pady": (10, 0), "sticky": "ew"},
        "ctts_and_save": {"row": 3, "column": 0, "padx": 30, "pady": (30, 0), "sticky": "ew"},
        "play_converted_speech_button": {"row": 4, "column": 0, "padx": 30, "pady": (17, 0), "sticky": "ew"},
    }

    def __init__(self):
        super().__init__()

        self.iconbitmap("icons/pikacon.ico") if platform.system() == 'Windows' else self.iconphoto(True, tkinter.PhotoImage(file="icons/pikacon.png"))
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("green")
        self.title("Speech Wich")
        self.geometry("700x375")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.locale_selection_window = None
        self.audio = None
        self.compact_mode = False
        self.config = self.load_config()
        self.set_values_from_config()

        self.method_to_play_audio = self.get_audio_method()
        if self.method_to_play_audio == "pygame":
            try:
                from pygame import mixer
                self.pygame_mixer = mixer
                self.pygame_mixer.init()
            except Exception as e:
                with open('logs', 'a') as f:
                    f.write(f"{e}\n")

        self.initialize_widgets()
        self.bind("<Configure>", self.on_window_configure)

        
    def initialize_widgets(self):
        # frame
        self.main_frame = customtkinter.CTkScrollableFrame(self)
        self.main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)

        # info label
        self.info_label = customtkinter.CTkLabel(self.main_frame, text="Made with love by Zai.", fg_color="transparent", text_color="pink")
        self.info_label.grid(**self.DEFAULT_MODE_SETTINGS["info_label"])

        # speed slider
        self.speed_slider = customtkinter.CTkSlider(self.main_frame, width=100, from_=-100, to=100, command=self.update_speed_value)
        self.speed_slider.grid(**self.DEFAULT_MODE_SETTINGS["speed_slider"])

        # speed value indicator label
        self.speed_value_indicator = customtkinter.CTkLabel(self.main_frame, text=f"voice speed: {int(self.speed_slider.get())}", fg_color="transparent", text_color="lightgreen")
        self.speed_value_indicator.grid(**self.DEFAULT_MODE_SETTINGS["speed_value_indicator"])

        # file name entry
        self.filename_entry = customtkinter.CTkEntry(self.main_frame, width=250, placeholder_text="Enter file name here (e.g my_audio_file)")
        self.filename_entry.grid(**self.DEFAULT_MODE_SETTINGS["filename_entry"])

        # locale changing window button
        self.select_locale_button = customtkinter.CTkButton(self.main_frame, width=70, height=30, text="Change locale", command=self.open_locale_selection_window)
        self.select_locale_button.grid(**self.DEFAULT_MODE_SETTINGS["select_locale_button"])

        # combobox for voices
        self.combobox_voices = customtkinter.CTkComboBox(self.main_frame, state="readonly", width=165, values=bing.voices[self.current_locale])
        self.combobox_voices.set(self.current_voice)
        self.combobox_voices.grid(**self.DEFAULT_MODE_SETTINGS["combobox_voices"])

        # input box
        self.input_textbox = customtkinter.CTkTextbox(self.main_frame, height=150)
        self.input_textbox.insert("0.0", "Enter text here, to convert Text-To-Speech.")
        self.input_textbox.grid(**self.DEFAULT_MODE_SETTINGS["input_textbox"])

        # button to ctts and save
        self.ctts_and_save = customtkinter.CTkButton(self.main_frame, text="Save", command=self.start_ctts_thread)
        self.ctts_and_save.grid(**self.DEFAULT_MODE_SETTINGS["ctts_and_save"])

        # button to ctts and play
        self.play_converted_speech_button = customtkinter.CTkButton(self.main_frame, text="Play", command=self.play_converted_speech)
        self.play_converted_speech_button.grid(**self.DEFAULT_MODE_SETTINGS["play_converted_speech_button"])

    def play_converted_speech(self):
        if self.play_converted_speech_button.cget('text') == "Play":
            filename = f"converted_audio/{sanitize_filename(self.filename_entry.get())}" + ".mp3"
            
            if filename == ".mp3":
                self.info_label.configure(text="Please enter a file name first.", text_color="red")
                return
            elif not os.path.exists(filename) and os.path.isfile(filename):
                self.info_label.configure(text=f"File {filename} not found.", text_color="red")
                return
            
            self.info_label.configure(text="Playing", text_color="lightgreen")
            self.play_converted_speech_button.configure(text="Stop")
            Thread(target=self.play_sound_thread, args=(filename,)).start()
        
        else:
            self.audio.stop() if self.method_to_play_audio == "pygame" else self.audio.kill()

    def play_sound_thread(self, filename):
        args_for_update_gui = {
            "info_label_text": "Stopped",
            "info_label_color": "pink",
            "play_button_text": "Play",
            "buttons_state": None
        }
        if self.method_to_play_audio == "pygame":
            self.audio = self.pygame_mixer.Sound(filename)
            self.audio.play()
            while self.pygame_mixer.get_busy():
                time.sleep(0.7)
        else:
            if platform.system() == "Windows":
                self.audio = subprocess.Popen([self.method_to_play_audio, filename], stdout=subprocess.PIPE, creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                self.audio = subprocess.Popen([self.method_to_play_audio, filename], stdout=subprocess.PIPE)
            self.audio.communicate()
        
        self.after(0, self.update_gui, args_for_update_gui)

    def start_ctts_thread(self):
        if not os.path.exists("converted_audio"):
            os.mkdir("converted_audio")
        filename = f"converted_audio/{sanitize_filename(self.filename_entry.get())}" + ".mp3"
        user_input = self.input_textbox.get('0.end', "end")
        voice = self.combobox_voices.get().split("(")[0].strip()

        if user_input == "\n":
            self.info_label.configure(text="Please enter some text.", text_color="red")
            return True
        if filename == ".mp3":
            self.info_label.configure(text="Please enter a valid file name.", text_color="red")
            return True

        self.ctts_and_save.configure(state="disabled")
        self.play_converted_speech_button.configure(state="disabled")
        self.info_label.configure(text_color="lightgreen", text="Converting, please wait...")

        self.update_last_voice_settings_values(self.current_locale, voice)
        Thread(target=self.perform_ctts, args=(user_input,
                                                filename,
                                                self.current_locale,
                                                voice,
                                                f"{int(self.speed_slider.get())}.00%"
                                                )).start()

    def perform_ctts(self, user_input, filename, locale, voice, speed_rate):
        args_for_update_gui = {
            "info_label_text": None,
            "info_label_color": None,
            "play_button_text": None,
            "buttons_state": "normal"
        }

        try:
            ssml = bing.split_text_and_build_ssml(text=user_input, locale=locale, voice=voice, speed_rate=speed_rate)
            error = bing.ctts(ssml, filename)
        except Exception as e:
            error = e

        if error is not None:
            with open("logs", "a") as f:
                f.write(str(str(error)) + "\n")

            args_for_update_gui["info_label_text"] = "Oops, looks like there was an error. Please check the logs file."
            args_for_update_gui["info_label_color"] = "red"
        else:
            args_for_update_gui["info_label_text"] = f"Saved in 'converted_audio' as {filename.split('/')[-1]}"
            args_for_update_gui["info_label_color"] = "lightgreen"

        self.after(0, self.update_gui, args_for_update_gui)

    def update_speed_value(self, value):
        self.speed_value_indicator.configure(text=f"voice speed: {int(value)}")

    def open_locale_selection_window(self):
        if self.locale_selection_window is None:
            self.locale_selection_window = localeSelectionWindow(self)
        else:
            if self.locale_selection_window.state() == "withdrawn":
                self.locale_selection_window.deiconify()
            else:
                self.locale_selection_window.focus()

    def update_locale(self, locale):
        self.combobox_voices.configure(values=bing.voices[locale])
        self.combobox_voices.set(bing.voices[locale][0])
        self.current_locale = locale
    
    def update_gui(self, args_for_update_gui):
        info_label_text = args_for_update_gui["info_label_text"]
        info_label_color = args_for_update_gui["info_label_color"]
        buttons_state = args_for_update_gui["buttons_state"]
        play_button_text = args_for_update_gui["play_button_text"]

        self.info_label.configure(text=info_label_text, text_color=info_label_color)
        if buttons_state:
            self.ctts_and_save.configure(state=buttons_state)
            self.play_converted_speech_button.configure(state=buttons_state)
        if play_button_text:
            self.play_converted_speech_button.configure(text=play_button_text)

    def turn_on_compact_mode(self):
        self.toggle_mode(self.COMPACT_MODE_SETTINGS)

    def turn_off_compact_mode(self):
        self.toggle_mode(self.DEFAULT_MODE_SETTINGS)
    
    def on_window_configure(self, event):
        current_width = self.main_frame.winfo_width()

        if current_width <= 570 and not self.compact_mode:
            self.compact_mode = True
            self.turn_on_compact_mode()
        elif current_width > 570 and self.compact_mode:
            self.compact_mode = False
            self.turn_off_compact_mode()
    
    def toggle_mode(self, mode_settings):
        for widget, settings in mode_settings.items():
            widget_instance = getattr(self, widget)
            widget_instance.grid_remove()
            widget_instance.grid(**settings)

    def get_audio_method(self):
        operating_system = platform.system()
        method_to_play_audio = self.AUDIO_METHODS.get(operating_system, "Other")

        if operating_system in ["Linux", "Darwin"]:
            if not self.is_tool_installed(method_to_play_audio):
                method_to_play_audio = "pygame"

        return method_to_play_audio
    
    @staticmethod
    def is_tool_installed(tool_name):
        try:
            subprocess.Popen([tool_name], stdout=subprocess.PIPE)
            return True
        except FileNotFoundError:
            return False

    def load_config(self):
        if not os.path.exists(self.CONFIG_FILE_PATH):
            config = configparser.ConfigParser()
            config['VoiceSettings'] = {
                'last_used_locale': 'en-US',
                'last_used_voice': 'en-US-AnaNeural (F, C)'
            }

            with open(self.CONFIG_FILE_PATH, 'w') as configfile:
                config.write(configfile)
        else:
            config = configparser.ConfigParser()
            config.read(self.CONFIG_FILE_PATH)

            if 'VoiceSettings' not in config:
                config['VoiceSettings'] = {}

            if 'last_used_locale' not in config['VoiceSettings']:
                config['VoiceSettings']['last_used_locale'] = 'en-US'

            if 'last_used_voice' not in config['VoiceSettings']:
                config['VoiceSettings']['last_used_voice'] = 'en-US-AnaNeural (F, C)'

            with open(self.CONFIG_FILE_PATH, 'w') as configfile:
                config.write(configfile)

        return config

    def set_values_from_config(self):
        self.current_locale = self.config['VoiceSettings']['last_used_locale']
        self.current_voice = self.config['VoiceSettings']['last_used_voice']

    def update_last_voice_settings_values(self, locale, voice):
        self.config['VoiceSettings']['last_used_locale'] = locale
        self.config['VoiceSettings']['last_used_voice'] = voice
        
        with open(self.CONFIG_FILE_PATH, 'w') as configfile:
            self.config.write(configfile)


if __name__ == "__main__":
    app = SpeechWich()
    app.mainloop()


#python3.11 -m venv .venv && source .venv/bin/activate && python3.11 -m pip install -r requirements.txt && python3.11 "Speech Wich.py
