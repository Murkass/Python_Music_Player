import customtkinter as ctk

class PlayingQueueFrame(ctk.CTkFrame):
    def __init__(self, master, data):
        super().__init__(master)
        self.master = master
        self.data = data
        self.currentDisplaying = []

        for i, value in enumerate(self.data):
            button = ctk.CTkButton(self, text=f"{i + 1}. {value['title']} - {value['time']}")
            button.grid(row=i, column=0, padx=10, pady=5, sticky="w")
            self.currentDisplaying.append(button)