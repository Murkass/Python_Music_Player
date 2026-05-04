import customtkinter as ctk
from PIL import Image, ImageTk

class LibraryFrame(ctk.CTkFrame):
    def __init__(self, master, data):
        super().__init__(master)
        self.master = master
        self.data = data
        self.currentDisplay = []

        for i, value in enumerate(self.data):

            img = Image.open(value['img']).resize((30, 30))
            tkImg = ImageTk.PhotoImage(img)
            label = self.CTkLabel(self, text=value['title'])
            label.image = tkImg 
            label.configure(compound="left")
            label.grid(row=i, column=0, padx=10, pady=5, sticky="w")
            self.currentDisplay.append(label)