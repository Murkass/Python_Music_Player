import customtkinter as ctk


class PlayingQueueFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, music_handler):
        super().__init__(master)
        self.master = master
        self.handler = music_handler
        self.currentDisplaying = []
        self.refresh()
        self._poll()

    def refresh(self):
        # Limpa conteúdo existente
        for w in list(self.winfo_children()):
            w.destroy()
        self.currentDisplaying = []

        # Mostra música atual
        try:
            if getattr(self.handler, 'currentPlaying', None):
                info = self.handler.getCurrentTrackInfo() or {}
                info_text = f"Tocando: {info.get('title','Unknown')} - {info.get('time','?')}"
                lbl = ctk.CTkLabel(self, text=info_text)
                lbl.pack(padx=8, pady=6, anchor='w')
        except Exception:
            pass

        queue = list(getattr(self.handler, 'playingQueue', []))
        for i, value in enumerate(queue):
            title = value.get('title', 'Unknown')
            t = value.get('time', '')
            btn = ctk.CTkButton(self, text=f"{i + 1}. {title} - {t}", command=lambda idx=i: self._on_click(idx))
            btn.pack(padx=10, pady=5, fill='x')
            self.currentDisplaying.append(btn)

    def _on_click(self, idx):
        try:
            self.handler.selectTrack(idx)
            self.refresh()
        except Exception as e:
            print(f"Error selecting track from queue: {e}")

    def _poll(self):
        try:
            self.refresh()
        except Exception:
            pass
        self.after(1000, self._poll)