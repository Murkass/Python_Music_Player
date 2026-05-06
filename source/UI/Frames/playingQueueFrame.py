import customtkinter as ctk

class PlayingQueueFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, data):
        super().__init__(master)
        self.master = master
        self.data = data
        self.currentDisplaying = []


        for i, value in enumerate(self.data):
            button = ctk.CTkButton(self, text=f"{i + 1}. {value['title']} - {value['time']}")
            button.configure(fg_color = "darkred", hover_color = "red", text_color = "white")
            button.pack(padx=10, pady=5, fill = "x")
            self.currentDisplaying.append(button)