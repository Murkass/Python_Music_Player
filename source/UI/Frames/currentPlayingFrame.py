import customtkinter as ctk

class CurrentPlayingFrame(ctk.CTkFrame):
    def __init__(self, master, data):
        super().__init__(master)
        self.master = master
        self.data = data
        self.rowconfigure((0, 1), weight=1)
        self.columnconfigure((0, 1 ,2), weight=1)
        
        if self.data:
            cDispData = ctk.CTkLabel(self, compound="left", text=f"{self.data['title']} - {self.data['artist']}")
            cDispData.grid(row=0, column=0, padx=10, pady=5, sticky="we")

            cBackBtn = ctk.CTkButton(self, text="<-", width=30)
            cBackBtn.grid(row=0, column=1, padx=10, pady=5, sticky="w")
            cplayBtn = ctk.CTkButton(self, text="||", width=30)
            cplayBtn.grid(row=0, column=1, padx=10, pady=5)
            cNextBtn = ctk.CTkButton(self, text="->", width=30)
            cNextBtn.grid(row=0, column=1, padx=10, pady=5, sticky="e")
