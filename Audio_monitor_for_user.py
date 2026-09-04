import customtkinter as ctk
from tkinter import colorchooser  # --- NEW: Imports the native Windows color palette ---
import threading
import time
import sys
import warnings

warnings.filterwarnings("ignore")

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class AudioMeterApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Audio Monitor")
        
        # --- Dimensions ---
        window_width = 240
        window_height = 110
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        x = screen_width - window_width - 20
        y = screen_height - window_height - 60
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.resizable(False, False)
        self.configure(fg_color="#ececec") 
        self.attributes("-topmost", True)
        self.overrideredirect(True)
        
        # --- Settings Icon ---
        self.lbl_settings = ctk.CTkLabel(self, text="⚙️", font=("Segoe UI", 20), cursor="hand2")
        self.lbl_settings.place(x=205, y=5)
        self.lbl_settings.bind("<ButtonPress-1>", self.open_settings)
        
        # --- Drag Logic Variables ---
        self._drag_start_x = 0
        self._drag_start_y = 0
        self.bind("<ButtonPress-1>", self.start_move)
        self.bind("<B1-Motion>", self.do_move)
        self.bind("<Button-3>", lambda e: self.on_closing())

        # --- Frames and Bars ---
        self.speaker_frame = ctk.CTkFrame(self, fg_color="#e0e0e0", corner_radius=15, height=35, width=210)
        self.speaker_frame.pack(pady=(15, 5))
        self.speaker_frame.pack_propagate(False) 
        
        self.lbl_speaker = ctk.CTkLabel(self.speaker_frame, text="🔊", font=("Segoe UI", 14), text_color="#333333")
        self.lbl_speaker.pack(side="left", padx=(15, 10))
        
        self.out_bar = ctk.CTkProgressBar(self.speaker_frame, width=140, height=8, corner_radius=4)
        self.out_bar.set(0) 
        self.out_bar.pack(side="left", padx=(0, 10))

        self.mic_frame = ctk.CTkFrame(self, fg_color="#e0e0e0", corner_radius=15, height=35, width=210)
        self.mic_frame.pack(pady=5)
        self.mic_frame.pack_propagate(False)

        self.lbl_mic = ctk.CTkLabel(self.mic_frame, text="🎤", font=("Segoe UI", 14), text_color="#333333")
        self.lbl_mic.pack(side="left", padx=(15, 10))
        
        self.in_bar = ctk.CTkProgressBar(self.mic_frame, width=140, height=8, corner_radius=4)
        self.in_bar.set(0)
        self.in_bar.pack(side="left", padx=(0, 10))

        for widget in (self.speaker_frame, self.mic_frame, self.lbl_speaker, self.lbl_mic):
            widget.bind("<ButtonPress-1>", self.start_move)
            widget.bind("<B1-Motion>", self.do_move)
            widget.bind("<Button-3>", lambda e: self.on_closing())

        self.running = True
        threading.Thread(target=self.monitor_mic, daemon=True).start()
        threading.Thread(target=self.monitor_speaker, daemon=True).start()

    # --- UI Customization Methods ---
    def open_settings(self, event):
        if hasattr(self, "settings_window") and self.settings_window.winfo_exists():
            self.settings_window.focus()
            return
            
        self.settings_window = ctk.CTkToplevel(self)
        self.settings_window.title("Aesthetics")
        self.settings_window.geometry("260x400")
        self.settings_window.attributes("-topmost", True)
        
        # Theme Toggle
        ctk.CTkLabel(self.settings_window, text="Theme").pack(pady=(10, 0))
        self.theme_switch = ctk.CTkSwitch(self.settings_window, text="Dark Mode", command=self.toggle_theme)
        if ctk.get_appearance_mode() == "Dark":
            self.theme_switch.select()
        self.theme_switch.pack(pady=5)

        # Ghost Mode Toggle
        ctk.CTkLabel(self.settings_window, text="Background Style").pack(pady=(10, 0))
        self.ghost_switch = ctk.CTkSwitch(self.settings_window, text="Ghost Mode", command=self.toggle_ghost)
        self.ghost_switch.pack(pady=5)

        # Opacity Slider
        ctk.CTkLabel(self.settings_window, text="Master Opacity").pack(pady=(10, 0))
        self.alpha_slider = ctk.CTkSlider(self.settings_window, from_=0.1, to=1.0, command=self.change_alpha)
        self.alpha_slider.set(self.attributes("-alpha"))
        self.alpha_slider.pack(pady=5)

        # --- NEW: Expanded Color Menu with 'Custom' option ---
        ctk.CTkLabel(self.settings_window, text="Accent Color").pack(pady=(10, 0))
        colors = ["blue", "green", "dark-blue", "red", "purple", "orange", "pink", "cyan", "yellow", "white", "black", "Custom"]
        self.color_menu = ctk.CTkOptionMenu(self.settings_window, values=colors, command=self.change_color)
        self.color_menu.pack(pady=5)

    def toggle_theme(self):
        is_dark = self.theme_switch.get() == 1
        
        if is_dark:
            ctk.set_appearance_mode("dark")
            self.configure(fg_color="#2b2b2b")
            self.speaker_frame.configure(fg_color="#404040")
            self.mic_frame.configure(fg_color="#404040")
            self.lbl_speaker.configure(text_color="#ffffff")
            self.lbl_mic.configure(text_color="#ffffff")
        else:
            ctk.set_appearance_mode("light")
            self.configure(fg_color="#ececec")
            self.speaker_frame.configure(fg_color="#e0e0e0")
            self.mic_frame.configure(fg_color="#e0e0e0")
            self.lbl_speaker.configure(text_color="#333333")
            self.lbl_mic.configure(text_color="#333333")
            
        if hasattr(self, 'ghost_switch') and self.ghost_switch.get() == 1:
            self.toggle_ghost()

    def toggle_ghost(self):
        if self.ghost_switch.get() == 1:
            bg_color = "#2b2b2b" if ctk.get_appearance_mode() == "Dark" else "#ececec"
            self.attributes("-transparentcolor", bg_color)
        else:
            self.attributes("-transparentcolor", "#000001")

    def change_alpha(self, value):
        self.attributes("-alpha", value)

    # --- NEW: Logic to handle the Custom Color Picker ---
    def change_color(self, value):
        if value == "Custom":
            # Opens the Windows color picker and grabs the hex code
            color_code = colorchooser.askcolor(title="Choose Accent Color")[1]
            if color_code:  # If the user selected a color and didn't hit 'Cancel'
                self.out_bar.configure(progress_color=color_code)
                self.in_bar.configure(progress_color=color_code)
        else:
            color_map = {
                "blue": "#1f6aa5", "green": "#2fa572", "dark-blue": "#003b6f",
                "red": "#e74c3c", "purple": "#8e44ad", "orange": "#e67e22",
                "pink": "#fd79a8", "cyan": "#00cec9", "yellow": "#f1c40f",
                "white": "#ffffff", "black": "#000000"
            }
            self.out_bar.configure(progress_color=color_map[value])
            self.in_bar.configure(progress_color=color_map[value])

    def start_move(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def do_move(self, event):
        x = self.winfo_pointerx() - self._drag_start_x
        y = self.winfo_pointery() - self._drag_start_y
        self.geometry(f"+{x}+{y}")

    def monitor_mic(self):
        import sounddevice as sd
        import numpy as np
        while self.running:
            try:
                with sd.InputStream(channels=1, samplerate=44100, blocksize=1024) as stream:
                    while self.running:
                        data, overflowed = stream.read(1024)
                        rms = np.sqrt(np.mean(data**2))
                        vol = min(rms * 10, 1.0) 
                        self.after(0, self.in_bar.set, vol)
            except Exception:
                time.sleep(1)

    def monitor_speaker(self):
        import comtypes
        from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
        from ctypes import cast, POINTER
        
        try:
            comtypes.CoInitialize()
        except Exception:
            pass
            
        while self.running:
            try:
                device = AudioUtilities.GetSpeakers()
                if device is None:
                    time.sleep(1)
                    continue
                    
                current_id = device.id
                interface = device._dev.Activate(IAudioMeterInformation._iid_, comtypes.CLSCTX_ALL, None)
                meter = cast(interface, POINTER(IAudioMeterInformation))
                
                check_counter = 0
                while self.running:
                    peak_value = meter.GetPeakValue()
                    self.after(0, self.out_bar.set, peak_value)
                    time.sleep(0.05)
                    
                    check_counter += 1
                    if check_counter >= 20: 
                        check_counter = 0
                        new_device = AudioUtilities.GetSpeakers()
                        if new_device is None or new_device.id != current_id:
                            break 
            except Exception:
                time.sleep(1)

    def on_closing(self):
        self.running = False
        self.destroy()
        sys.exit()

if __name__ == "__main__":
    app = AudioMeterApp()
    app.mainloop()