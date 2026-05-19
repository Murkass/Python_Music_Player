import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from .storeHandler import StoreHandler

class LibraryHandler:
    """
    Gerencia a biblioteca de músicas e playlists.
    Responsável por salvar, carregar, modificar e organizar playlists no JSON.
    """
    
    def __init__(self, storeHandler: StoreHandler):
        """
        Inicializa o handler com o caminho do arquivo de biblioteca.
        
        Args:
            library_path: Caminho do arquivo library.json
        """
        self.handler = storeHandler
        # carregar dados existentes das chaves top-level (compatível com formato atual)
        sd = getattr(self.handler, 'store_data', {}) or {}
        playlists = sd.get('playlists', {})
        settings = sd.get('settings', {})
        history = sd.get('history', [])
        # garantir tipos esperados
        self.library_data = {
            'playlists': playlists if isinstance(playlists, dict) else {},
            'settings': settings if isinstance(settings, dict) else {},
            'history': history if isinstance(history, list) else []
        }
    
    def _save_library(self) -> bool:
        """Salva a biblioteca no JSON."""
        try:
            # Atualizar keys top-level para compatibilidade com o formato existente
            try:
                self.handler.set_storageData('playlists', self.library_data.get('playlists', {}))
                self.handler.set_storageData('history', self.library_data.get('history', []))
                self.handler.set_storageData('settings', self.library_data.get('settings', {}))
            except Exception:
                # fallback direto
                self.handler.store_data['playlists'] = self.library_data.get('playlists', {})
                self.handler.store_data['history'] = self.library_data.get('history', [])
                self.handler.store_data['settings'] = self.library_data.get('settings', {})

            return self.handler._save_store()
        except Exception as e:
            print(f"Erro ao salvar biblioteca: {e}")
            return False
    
    def create_playlist(self, playlist_name: str) -> bool:
        """
        Cria uma nova playlist.
        
        Args:
            playlist_name: Nome da playlist
            
        Returns:
            True se criada com sucesso, False se já existe
        """
        if playlist_name in self.library_data.get("playlists", {}):
            print(f"Playlist '{playlist_name}' já existe.")
            return False
        self.library_data["playlists"][playlist_name] = {
            "musics": [],
            "created_at": datetime.utcnow().isoformat()
        }
        return self._save_library()
    
    def add_music_to_playlist(self, playlist_name: str, music_path: str, title: str = None, artist: str = None) -> bool:
        """
        Adiciona uma música a uma playlist.
        
        Args:
            playlist_name: Nome da playlist
            music_path: Caminho da música
            title: Título da música (opcional)
            artist: Artista da música (opcional)
            
        Returns:
            True se adicionada com sucesso
        """
        if playlist_name not in self.library_data["playlists"]:
            print(f"Playlist '{playlist_name}' não existe.")
            return False
        
        music_entry = {
            "path": music_path,
            "title": title or os.path.basename(music_path),
            "artist": artist or "Unknown"
        }
        
        self.library_data["playlists"][playlist_name]["musics"].append(music_entry)
        return self._save_library()
    
    def remove_music_from_playlist(self, playlist_name: str, music_index: int) -> bool:
        """
        Remove uma música de uma playlist.
        
        Args:
            playlist_name: Nome da playlist
            music_index: Índice da música na playlist
            
        Returns:
            True se removida com sucesso
        """
        if playlist_name not in self.library_data["playlists"]:
            print(f"Playlist '{playlist_name}' não existe.")
            return False
        
        if not (0 <= music_index < len(self.library_data["playlists"][playlist_name]["musics"])):
            print(f"Índice inválido: {music_index}")
            return False
        
        self.library_data["playlists"][playlist_name]["musics"].pop(music_index)
        return self._save_library()
    
    def reorder_music(self, playlist_name: str, old_index: int, new_index: int) -> bool:
        """
        Altera a ordem de uma música na playlist.
        
        Args:
            playlist_name: Nome da playlist
            old_index: Índice atual
            new_index: Novo índice
            
        Returns:
            True se reordenada com sucesso
        """
        if playlist_name not in self.library_data["playlists"]:
            print(f"Playlist '{playlist_name}' não existe.")
            return False
        
        musics = self.library_data["playlists"][playlist_name]["musics"]
        
        if not (0 <= old_index < len(musics) and 0 <= new_index < len(musics)):
            print(f"Índices inválidos: old={old_index}, new={new_index}")
            return False
        
        music = musics.pop(old_index)
        musics.insert(new_index, music)
        return self._save_library()
    
    def get_playlist(self, playlist_name: str) -> Optional[Dict]:
        """
        Retorna uma playlist completa.
        
        Args:
            playlist_name: Nome da playlist
            
        Returns:
            Dados da playlist ou None se não existe
        """
        return self.library_data["playlists"].get(playlist_name)
    
    def get_all_playlists(self) -> List[str]:
        """Retorna lista de nomes de todas as playlists."""
        return list(self.library_data["playlists"].keys())
    
    def delete_playlist(self, playlist_name: str) -> bool:
        """
        Deleta uma playlist.
        
        Args:
            playlist_name: Nome da playlist
            
        Returns:
            True se deletada com sucesso
        """
        if playlist_name not in self.library_data["playlists"]:
            print(f"Playlist '{playlist_name}' não existe.")
            return False
        
        del self.library_data["playlists"][playlist_name]
        return self._save_library()
    
    def get_playlist_musics(self, playlist_name: str) -> List[Dict]:
        """
        Retorna lista de músicas de uma playlist.
        
        Args:
            playlist_name: Nome da playlist
            
        Returns:
            Lista de músicas
        """
        playlist = self.get_playlist(playlist_name)
        return playlist["musics"] if playlist else []
