import customtkinter as ctk

class CurrentPlayingFrame(ctk.CTkFrame):
    def __init__(self, master, data):
        super().__init__(master)
        self.master = master
        self.data = data

        self.currentDisplaying = None
        
        if self.data:
            self.currentDisplaying = ctk.CTkLabel(self, text=f"{self.data['title']} - {self.data['artist']}")
            self.currentDisplaying.grid(row=0, column=0, padx=10, pady=5, sticky="we")