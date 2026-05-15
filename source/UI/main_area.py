import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from source.core.libraryHandler import LibraryHandler
from source.core.musicHandler import MusicHandler
from typing import Optional
import os
import mutagen


class MainAreaFrame(ctk.CTkFrame):
    def __init__(self, master, music_handler: MusicHandler, library_handler: Optional[LibraryHandler] = None):
        super().__init__(master)
        self.handler = music_handler
        self.library = library_handler or LibraryHandler()
        self.selected_playlist: Optional[str] = None
        self.playlists = []
        self.songs = []
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        self._build_ui()
        self._load_playlists()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="we", padx=8, pady=6)
        header.grid_columnconfigure(0, weight=1)

        title = ctk.CTkLabel(header, text="Biblioteca", font=(None, 18, "bold"))
        title.grid(row=0, column=0, sticky="w", padx=(10, 0))

        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.grid(row=0, column=1, sticky="e", padx=10)
        self.show_all_btn = ctk.CTkButton(btn_frame, text="Ver Todas Músicas", command=self._show_all_musics, width=150)
        self.show_all_btn.pack(side="left", padx=6)
        add_btn = ctk.CTkButton(btn_frame, text="Adicionar Música", command=self._add_music_to_library)
        add_btn.pack(side="left", padx=6)
        create_pl_btn = ctk.CTkButton(btn_frame, text="Criar Playlist", command=self._create_playlist)
        create_pl_btn.pack(side="left", padx=6)

        # Selected playlist label and play button (row below)
        self.selected_label = ctk.CTkLabel(header, text="Todas as músicas", font=(None, 14))
        self.selected_label.grid(row=1, column=0, sticky="w", padx=(10, 0), pady=(4, 0))

        self.play_playlist_btn = ctk.CTkButton(header, text="Play Playlist", command=self._play_playlist, width=120)
        self.play_playlist_btn.grid(row=1, column=1, sticky="e", padx=10, pady=(4, 0))
        self.play_playlist_btn.configure(state="disabled")

        # Apenas área principal de músicas (a lista de playlists fica em LibraryFrame)
        right = ctk.CTkFrame(self)
        right.grid(row=1, column=0, sticky="nswe", padx=8, pady=6)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        songs_label = ctk.CTkLabel(right, text="Músicas")
        songs_label.grid(row=0, column=0, sticky="nw", padx=6, pady=(6, 0))
        self.songs_listbox = tk.Listbox(right, exportselection=False)
        self.songs_listbox.grid(row=1, column=0, sticky="nswe", padx=6, pady=6)
        song_scroll = tk.Scrollbar(right, command=self.songs_listbox.yview)
        song_scroll.grid(row=1, column=1, sticky="ns", pady=6)
        self.songs_listbox.config(yscrollcommand=song_scroll.set)
        self.songs_listbox.bind("<Double-Button-1>", lambda e: self._play_selected_track())

        actions = ctk.CTkFrame(right, fg_color="transparent")
        actions.grid(row=2, column=0, sticky="we", padx=6, pady=6)
        add_to_pl = ctk.CTkButton(actions, text="Adicionar à Playlist", command=self._add_selected_to_playlist)
        add_to_pl.pack(side="left", padx=6)
        remove_btn = ctk.CTkButton(actions, text="Remover", command=self._remove_selected_music)
        remove_btn.pack(side="left", padx=6)
        update_btn = ctk.CTkButton(actions, text="Editar", command=self._update_selected_music)
        update_btn.pack(side="left", padx=6)

    def _load_playlists(self):
        self.playlists = self.library.get_all_playlists()
        self.selected_playlist = None
        self._show_all_musics()

    

    def _populate_songs(self, musics):
        self.songs = musics
        self.songs_listbox.delete(0, tk.END)
        for m in musics:
            display = f"{m.get('title','Unknown')} - {m.get('artist','Unknown')}"
            self.songs_listbox.insert(tk.END, display)

    def _scan_music_folder(self):
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        mus_dir = os.path.join(base_dir, 'musics')
        if not os.path.exists(mus_dir):
            return []
        musics = []
        for root, _, files in os.walk(mus_dir):
            for f in files:
                if f.lower().endswith(('.mp3', '.wav', '.flac', '.ogg', '.m4a')):
                    path = os.path.join(root, f)
                    title = None
                    artist = None
                    try:
                        audio = mutagen.File(path)
                        tags = getattr(audio, 'tags', None)
                        if tags:
                            if 'TIT2' in tags:
                                title = str(tags['TIT2'])
                            elif 'title' in tags:
                                t = tags.get('title')
                                title = t[0] if isinstance(t, (list, tuple)) else str(t)
                            if 'TPE1' in tags:
                                artist = str(tags['TPE1'])
                            elif 'artist' in tags:
                                a = tags.get('artist')
                                artist = a[0] if isinstance(a, (list, tuple)) else str(a)
                    except Exception:
                        pass
                    if not title:
                        title = os.path.splitext(f)[0]
                    if not artist:
                        artist = 'Unknown'
                    musics.append({
                        'path': path,
                        'title': title,
                        'artist': artist
                    })
        return musics

    def _show_all_musics(self):
        musics = self._scan_music_folder()
        self.selected_playlist = None
        self.selected_label.configure(text="Todas as músicas")
        self.play_playlist_btn.configure(state="disabled")
        self._populate_songs(musics)

    def select_playlist(self, playlist_name: str):
        self.selected_playlist = playlist_name
        self.selected_label.configure(text=f"Playlist: {playlist_name}")
        self.play_playlist_btn.configure(state="normal")
        musics = self.library.get_playlist_musics(playlist_name)
        self._populate_songs(musics)

    def _play_playlist(self):
        if not self.selected_playlist:
            messagebox.showwarning("Aviso", "Selecione uma playlist primeiro.")
            return
        pl = self.library.get_playlist(self.selected_playlist)
        if pl:
            self.handler.selectPlaylist(pl)
            try:
                if hasattr(self.master, 'playingQueueFrame') and getattr(self.master, 'playingQueueFrame') is not None:
                    self.master.playingQueueFrame.refresh()
            except Exception:
                pass

    def _add_music_to_library(self):
        path = filedialog.askopenfilename(title="Selecione arquivo de áudio", filetypes=[("Áudio", "*.mp3 *.wav *.flac"),("All files","*.*")])
        if not path:
            return
        title = simpledialog.askstring("Título", "Título da música (opcional):")
        artist = simpledialog.askstring("Artista", "Artista da música (opcional):")
        target_playlists = self.library.get_all_playlists()
        if not target_playlists:
            self.library.create_playlist("Padrão")
            target_playlists = self.library.get_all_playlists()
        self.library.add_music_to_playlist(target_playlists[0], path, title, artist)
        self._load_playlists()
        messagebox.showinfo("Sucesso", "Música adicionada à biblioteca.")

    def _create_playlist(self):
        name = simpledialog.askstring("Nova Playlist", "Nome da playlist:")
        if not name:
            return
        ok = self.library.create_playlist(name)
        if ok:
            self._load_playlists()
        else:
            messagebox.showwarning("Aviso", f"Playlist '{name}' já existe ou não pôde ser criada.")

    def _get_selected_song(self):
        sel = self.songs_listbox.curselection()
        if not sel:
            return None, None
        index = sel[0]
        if index < len(self.songs):
            return index, self.songs[index]
        return None, None

    def _add_selected_to_playlist(self):
        index, mus = self._get_selected_song()
        if mus is None:
            messagebox.showwarning("Aviso", "Selecione uma música primeiro.")
            return
        target = simpledialog.askstring("Adicionar à Playlist", "Nome da playlist destino:")
        if not target:
            return
        ok = self.library.add_music_to_playlist(target, mus.get("path"), mus.get("title"), mus.get("artist"))
        if ok:
            messagebox.showinfo("Sucesso", f"Música adicionada à playlist '{target}'.")
        else:
            messagebox.showwarning("Erro", f"Não foi possível adicionar música à playlist '{target}'.")

    def _remove_selected_music(self):
        if not self.selected_playlist:
            messagebox.showwarning("Aviso", "Remoção só disponível em uma playlist selecionada.")
            return
        sel = self.songs_listbox.curselection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma música para remover.")
            return
        idx = sel[0]
        ok = self.library.remove_music_from_playlist(self.selected_playlist, idx)
        if ok:
            # refresh view for the current playlist
            self.select_playlist(self.selected_playlist)
        else:
            messagebox.showwarning("Erro", "Não foi possível remover a música.")

    def _update_selected_music(self):
        if not self.selected_playlist:
            messagebox.showwarning("Aviso", "Edição só disponível em uma playlist selecionada.")
            return
        idx, mus = self._get_selected_song()
        if mus is None:
            messagebox.showwarning("Aviso", "Selecione uma música para editar.")
            return
        new_title = simpledialog.askstring("Título", "Novo título:", initialvalue=mus.get("title"))
        new_artist = simpledialog.askstring("Artista", "Novo artista:", initialvalue=mus.get("artist"))
        if new_title is None and new_artist is None:
            return
        pl = self.library.get_playlist(self.selected_playlist)
        if pl and 0 <= idx < len(pl["musics"]):
            if new_title is not None:
                pl["musics"][idx]["title"] = new_title
            if new_artist is not None:
                pl["musics"][idx]["artist"] = new_artist
            self.library._save_library()
            # refresh view for the current playlist
            self.select_playlist(self.selected_playlist)

    def _play_selected_track(self):
        idx, mus = self._get_selected_song()
        if mus is None:
            return
        if self.selected_playlist:
            pl = self.library.get_playlist(self.selected_playlist)
            if pl:
                self.handler.selectPlaylist(pl)
        else:
            temp_pl = {"musics": self.songs}
            self.handler.selectPlaylist(temp_pl)
        self.handler.selectTrack(0 if idx is None else idx)
        try:
            if hasattr(self.master, 'playingQueueFrame') and getattr(self.master, 'playingQueueFrame') is not None:
                self.master.playingQueueFrame.refresh()
        except Exception:
            pass
