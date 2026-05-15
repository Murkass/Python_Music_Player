import customtkinter as ctk
from source.core.musicHandler import MusicHandler
#TODO: Pequena mudança de intenção ao inves de "deslizar" o WaveForm,
# vamos vazer um audio spectrum analyzer com o ctkCanvas criando varias barras que aumentaram de tamanho baseado na no "frame da musica no momento"
#Em compensação vai ser bem mais leve utilizar do que o matplot, e vai ser bem fluido se feito direto
#O problema vai ser fazer direito e acertar na arquitetura para dividir o que vai ser as funções e o que vai ser CTKWidget

class CurrentPlayingFrame(ctk.CTkFrame):
    def __init__(self, master, musicHandler: MusicHandler):
        super().__init__(master)
        self.master = master
        self.handler = musicHandler
        self.rowconfigure((0, 1), weight=1)
        self.columnconfigure((0, 2), weight=1)
        self.columnconfigure(1, weight=3)
        
        if self.data:
            cDispData = ctk.CTkLabel(self, compound="left", text=f"{self.data['title']} - {self.data['artist']}")
            cDispData.grid(row=0, column=0, padx=10, pady=5, sticky="we")

            # Frame para conter os botões de controle
            cControlFrame = ctk.CTkFrame(self, fg_color="transparent")
            cControlFrame.grid(row=0, column=1, padx=10, pady=5)
            
            cBackBtn = ctk.CTkButton(cControlFrame, text="<-", width=30)
            cBackBtn.pack(side="left", padx=5)
            cplayBtn = ctk.CTkButton(cControlFrame, text="||", width=30)
            cplayBtn.pack(side="left", padx=5)
            cNextBtn = ctk.CTkButton(cControlFrame, text="->", width=30)
            cNextBtn.pack(side="left", padx=5)

            cPlaceholder = ctk.CTkLabel(self, compound="right",text="Testestetestset")
            cPlaceholder.grid(row=0, column=2, padx=10, pady=5, sticky="we")
            
            cDispPrg = ctk.CTkCanvas(self, width=self._current_width, height=(self._current_height/2), highlightthickness=0, bg=f"{self.cget("fg_color")[1]}")
            cDispPrg.grid(row=1, column=1, padx=10, pady=5, sticky="we")

            cDispPrg_bars = [cDispPrg.create_rectangle(i*20, (self._current_height/2) - 4, (i*20)+15, self._current_height/2, fill="blue") for i in range(20)]

    
