from . import *
import customtkinter as ctk

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("800x600")
        self.title("CustomTkinter Example")

        self.frame = Frames.mainFrame(self, data={
            "current": {"title": "Song Title", "artist": "Artist Name"}, 
            "queue": [
                {"title": "Next Song 1", "time": "3:45"}, 
                {"title": "Next Song 2", "time": "4:20"}
            ], 
            "library": [
                {"title": "Song 1", "artist": "Artist 1"}, 
                {"title": "Song 2", "artist": "Artist 2"}
            ]
        })
        self.frame.pack(fill="both", expand=True)
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")  # Modes: "System" (default), "Dark", "Light"
    app = App()

    app.mainloop()