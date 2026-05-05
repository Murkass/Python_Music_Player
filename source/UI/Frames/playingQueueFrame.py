import customtkinter as ctk

class PlayingQueueFrame(ctk.CTkFrame):
    def __init__(self, master, data):
        super().__init__(master)
        self.master = master
        self.data = data
        self.currentDisplaying = []

        for i, value in enumerate(self.data):
            label = ctk.CTkLabel(self, text=f"{i + 1}. {value['title']} - {value['time']}")
            label.grid(row=i, column=0, padx=10, pady=5, sticky="w")
            self.currentDisplaying.append(label)