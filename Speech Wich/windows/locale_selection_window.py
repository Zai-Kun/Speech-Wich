import customtkinter, tkinter
from btts import Bing

bing = Bing()

class localeSelectionWindow(customtkinter.CTkToplevel):
    def __init__(self, main_class, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_class = main_class 
        self.geometry("300x400")
        self.title("Speech Wich")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # fain frame
        self.main_frame = customtkinter.CTkScrollableFrame(self)
        self.main_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)

        # label
        self.info_label = customtkinter.CTkLabel(self.main_frame, text="Select a locale", fg_color="transparent", text_color="pink")
        self.info_label.grid(row=0, column=0, padx=0, pady=0, sticky="n")

        #search bar entry
        self.search_bar = customtkinter.CTkEntry(self.main_frame, placeholder_text="Search here")
        self.search_bar.grid(row=1, column=0, padx=8, pady=(0, 10), sticky="ew")

        #search button
        self.search_button = customtkinter.CTkButton(self.main_frame, text="Search", command=self.search)
        self.search_button.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")

        # radio buttons
        self.locale_radio_buttons_var = tkinter.StringVar(value=self.main_class.current_locale)
        self.locale_radio_buttons = []

        for i, locale in enumerate(bing.voices):
            radio_button = customtkinter.CTkRadioButton(self.main_frame, text=locale, variable=self.locale_radio_buttons_var, value=locale, command=lambda: self.main_class.update_locale(self.locale_radio_buttons_var.get()))
            radio_button.grid(row=i+3, column=0, pady=5)
            self.locale_radio_buttons.append(radio_button)
        
        self.protocol("WM_DELETE_WINDOW", self.withdraw)

    def search(self):
        query = self.search_bar.get()
        if len([locale for locale in bing.voices if query.lower() in locale.lower()]) == 0:
            self.info_label.configure(text="Not found.", text_color="red")
            return

        row = 3

        def grid(radio_button):
            button_grided = radio_button.grid_info()
            if not button_grided:
                radio_button.grid(row=row, column=0, pady=5)
                return True
        
        def ungrid(radio_button):
            button_grided = radio_button.grid_info()
            if button_grided:
                radio_button.grid_remove()
        
        if query == "":
            for radio_button in self.locale_radio_buttons:
                ungrid(radio_button)
            
            for radio_button in self.locale_radio_buttons:
                grid(radio_button)
                row += 1
            return

        
        for radio_button in self.locale_radio_buttons:
            button_value = radio_button.cget("value")

            if query.lower() in button_value.lower():
                if grid(radio_button):
                    row += 1
            else:
                ungrid(radio_button)

        self.info_label.configure(text="Found.", text_color="lightgreen")