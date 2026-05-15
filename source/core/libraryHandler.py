import json
import os
from pathlib import Path
from typing import List, Dict, Optional

class LibraryHandler:
    """
    Gerencia a biblioteca de músicas e playlists.
    Responsável por salvar, carregar, modificar e organizar playlists no JSON.
    """
    
    def __init__(self, library_path: str = "source/core/library.json"):
        """
        Inicializa o handler com o caminho do arquivo de biblioteca.
        
        Args:
            library_path: Caminho do arquivo library.json
        """
        self.library_path = library_path
        self.library_data = self._load_library()
    
    def _load_library(self) -> Dict:
        """Carrega a biblioteca do JSON ou cria uma nova estrutura."""
        if os.path.exists(self.library_path):
            try:
                with open(self.library_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data if data else self._create_default_structure()
            except (json.JSONDecodeError, IOError):
                return self._create_default_structure()
        return self._create_default_structure()
    
    def _create_default_structure(self) -> Dict:
        """Cria a estrutura padrão da biblioteca."""
        return {
            "playlists": {}
        }
    
    def _save_library(self) -> bool:
        """Salva a biblioteca no JSON."""
        try:
            os.makedirs(os.path.dirname(self.library_path) or ".", exist_ok=True)
            with open(self.library_path, 'w', encoding='utf-8') as f:
                json.dump(self.library_data, f, indent=4, ensure_ascii=False)
            return True
        except IOError as e:
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
        if playlist_name in self.library_data["playlists"]:
            print(f"Playlist '{playlist_name}' já existe.")
            return False
        
        self.library_data["playlists"][playlist_name] = {
            "musics": [],
            "created_at": str(Path(self.library_path).stat().st_mtime if os.path.exists(self.library_path) else 0)
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
