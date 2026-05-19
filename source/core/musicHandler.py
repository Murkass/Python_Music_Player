import mutagen
import pygame.mixer as mixer
from collections import deque
import os
import numpy as np
import soundfile as sf
from threading import Lock
from datetime import datetime

from .storeHandler import StoreHandler

CHUNK_SIZE = 1024 # Tamanho do bloco de áudio lido por vez

class MusicHandler:
    def __init__(self, storeHandler: StoreHandler):
        self.currentPlaying = None
        self.playingQueue = deque()
        # historic holds most-recent first (appendleft)
        self.historic = deque(maxlen=50)
        self._lock = Lock()
        self.paused = False
        self.storeHandler = storeHandler
        # carregar histórico persistido (se houver) — compatível com 'history' top-level
        try:
            sd = getattr(self.storeHandler, 'store_data', {}) or {}
            stored = sd.get('history') or sd.get('historic') or []
            if isinstance(stored, list) and stored:
                # normalizar entradas para formato interno (filePath/title/artist/time)
                normalized = []
                for item in stored:
                    if not isinstance(item, dict):
                        continue
                    path = item.get('path') or item.get('filePath') or item.get('file_path')
                    title = item.get('title')
                    artist = item.get('artist')
                    time_str = item.get('time') or item.get('duration') or ''
                    normalized.append({
                        'filePath': path,
                        'title': title,
                        'artist': artist,
                        'time': time_str
                    })
                self.historic = deque(normalized, maxlen=50)
        except Exception:
            pass
        mixer.init()
        mixer.music.set_volume(0.5)

    def _persist_historic(self):
        """Persiste o histórico atual no StoreHandler (store.json)."""
        try:
            # converter deque para lista serializável
            hist_list = []
            for item in list(self.historic):
                if not isinstance(item, dict):
                    continue
                path = item.get('filePath') or item.get('path') or item.get('file_path')
                hist_list.append({
                    'path': path,
                    'title': item.get('title'),
                    'artist': item.get('artist'),
                    'played_at': item.get('played_at') or datetime.utcnow().isoformat()
                })

            # gravar no store sob a chave top-level 'history' (compatível)
            try:
                if hasattr(self.storeHandler, 'set_storageData'):
                    self.storeHandler.set_storageData('history', hist_list)
                else:
                    self.storeHandler.store_data['history'] = hist_list
            except Exception:
                self.storeHandler.store_data['history'] = hist_list

            # forçar salvar
            if hasattr(self.storeHandler, '_save_store'):
                try:
                    self.storeHandler._save_store()
                except Exception:
                    pass
        except Exception as e:
            print(f"Error persisting historic: {e}")

    def addToQueue(self, _filePath, _title, _artist):
        try:
            audio = mutagen.File(_filePath)
            title = _title if _title is not None else audio.get("TIT2", "Unknown Title")
            artist = _artist if _artist is not None else audio.get("TPE1", "Unknown Artist")
            time = int(audio.info.length)
            minutes = time // 60
            seconds = time % 60
            formatted_time = f"{minutes}:{seconds:02d}"
            self.playingQueue.append({
                "filePath": _filePath,
                "title": title,
                "artist": artist,
                "time": formatted_time
            })

            if(not self.currentPlaying):
                self.selectTrack(0)

        except Exception as e:
            print(f"Error adding to queue: {e}")

    def clearQueue(self):
        with self._lock:
            self.playingQueue.clear()
            self.historic.clear()
            self.currentPlaying = None
            # persistir histórico vazio
            try:
                self._persist_historic()
            except Exception:
                pass
        mixer.music.stop()

    def selectPlaylist(self, playlistObj):
        self.clearQueue()
        for mus in playlistObj["musics"]:
            self.addToQueue(mus["path"], mus["title"], mus["artist"])
        
    def getCurrentTrackInfo(self):
        if self.currentPlaying:
            return {
                "title": self.currentPlaying.get("title", "Unknown Title"),
                "artist": self.currentPlaying.get("artist", "Unknown Artist"),
                "time": self.currentPlaying.get("time", "0:00")
            }
        return None

    def playNext(self):
        try:
            if self.playingQueue:
                if self.currentPlaying:
                    # registrar metadados de reprodução com timestamp
                    hist_item = dict(self.currentPlaying) if isinstance(self.currentPlaying, dict) else {
                        'filePath': getattr(self.currentPlaying, 'filePath', None)
                    }
                    hist_item['played_at'] = datetime.utcnow().isoformat()
                    with self._lock:
                        self.historic.appendleft(hist_item)
                        try:
                            self._persist_historic()
                        except Exception:
                            pass
                self.currentPlaying = self.playingQueue.popleft()
                mixer.music.load(self.currentPlaying["filePath"])
                mixer.music.play()
                return self.getCurrentTrackInfo()
        except Exception as e:
            print(f"Error playing next track: {e}")

    def playPrevious(self):
        try:
            if self.historic:
                if self.currentPlaying:
                    self.playingQueue.appendleft(self.currentPlaying)
                with self._lock:
                    self.currentPlaying = self.historic.popleft()
                    # ao remover do histórico, já persistido anteriormente, apenas atualizar store
                    try:
                        self._persist_historic()
                    except Exception:
                        pass
                mixer.music.load(self.currentPlaying["filePath"])
                mixer.music.play()
                return self.getCurrentTrackInfo()
        except Exception as e:
            mixer.music.load(self.currentPlaying["filePath"])
            mixer.music.play()
            print(f"Error playing previous track: {e}")

    def playPause(self):
        try:
            if self.paused:
                mixer.music.unpause()
                self.paused = False
            else:
                mixer.music.pause()
                self.paused = True
        except Exception as e:
            print(f"Error toggling play/pause: {e}")

    def selectTrack(self, index):
        try:
            if 0 <= index < len(self.playingQueue):
                if self.currentPlaying:
                    hist_item = dict(self.currentPlaying) if isinstance(self.currentPlaying, dict) else {
                        'filePath': getattr(self.currentPlaying, 'filePath', None)
                    }
                    hist_item['played_at'] = datetime.utcnow().isoformat()
                    with self._lock:
                        self.historic.appendleft(hist_item)
                        try:
                            self._persist_historic()
                        except Exception:
                            pass
                self.currentPlaying = self.playingQueue[index]
                mixer.music.load(self.currentPlaying["filePath"])
                mixer.music.play()
                for i in list(self.playingQueue):
                    if self.playingQueue.index(i) >= index:
                        self.playingQueue.remove(i)
        except Exception as e:
            print(f"Error selecting track: {e}")
    
    def setVol(self, volume):
        if(0 <= volume <= 1):
            mixer.music.set_volume(volume)
            return self.getVol()
        else:
            print("invalid set value")

    def getVol(self):
        return mixer.music.get_volume()

    def getCurrentPosition(self):
        """Retorna a posição atual da reprodução em segundos."""
        try:
            pos_ms = mixer.music.get_pos()
            if pos_ms is None or pos_ms < 0:
                return 0.0
            return pos_ms / 1000.0
        except Exception as e:
            print(f"Error getting current position: {e}")
            return 0.0

    def getSpectrumData(self, filePath, window_ms: int = 200):
        """
        Retorna magnitudes aproximadas do espectro no ponto atual da música.
        Lê uma janela curta do arquivo a partir da posição atual.
        """
        try:
            info = sf.info(filePath)
            samplerate = info.samplerate
            pos_ms = mixer.music.get_pos()
            if pos_ms is None or pos_ms < 0:
                pos_ms = 0

            # Janela centrada na posição atual
            start_ms = max(0, int(pos_ms - window_ms // 2))
            start_frame = int(start_ms * samplerate / 1000)
            frames = int(window_ms * samplerate / 1000)

            data, sr = sf.read(filePath, start=start_frame, frames=frames, dtype='float32')
            if data is None or getattr(data, 'size', 0) == 0:
                return np.array([])

            if data.ndim > 1:
                data = data.mean(axis=1)

            # Aplica janela para reduzir leakage
            if len(data) > 1:
                window = np.hanning(len(data))
                data = data * window

            fft_res = np.fft.rfft(data)
            magnitudes = np.abs(fft_res)
            return magnitudes
        except Exception as e:
            print(f"Error getting spectrum: {e}")
            return np.array([])