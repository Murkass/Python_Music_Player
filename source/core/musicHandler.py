import mutagen
import pygame.mixer as mixer
from collections import deque
import os
import numpy as np
import soundfile as sf
"""
TODO: Criar forma de gerenciar um multiProcessos com PID, com lock para não tocar mais de uma vez
E fazer com que renderize o waveform dentro do customTkinter com o matplotlib, usando o canvas do customTkinter para renderizar o gráfico, e não abrir uma janela separada
Arrumar a parte das pastas com dir_name para facilitar e não precisar do caminho absoluto
Ah, arrumar esses importes nada haver
"""

CHUNK_SIZE = 1024 # Tamanho do bloco de áudio lido por vez

class MusicHandler:
    def __init__(self):
        self.currentPlaying = None
        self.playingQueue = deque()
        self.historic = deque(maxlen=50)
        self.paused = False
        mixer.init()
        mixer.music.set_volume(0.5)

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
        self.playingQueue.clear()
        self.historic.clear()
        self.currentPlaying = None
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
                self.historic.appendleft(self.currentPlaying) if self.currentPlaying else None
                self.currentPlaying = self.playingQueue.popleft()
                mixer.music.load(self.currentPlaying["filePath"])
                mixer.music.play()
                return self.getCurrentTrackInfo()
        except Exception as e:
            print(f"Error playing next track: {e}")

    def playPrevious(self):
        try:
            if self.historic:
                self.playingQueue.appendleft(self.currentPlaying) if self.currentPlaying else None
                self.currentPlaying = self.historic.popleft()
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
                self.historic.appendleft(self.currentPlaying) if self.currentPlaying else None
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

    def getSpectrumData(self, filePath):
        samplerate = sf.info(filePath)
        miliseconds = mixer.music.get_pos()
        currentFrame = (samplerate * miliseconds) / 1000
        data = sf.read(file=filePath, frames=currentFrame)

        if(mixer.music.get_endevent()):
            return []

        fft_res = np.fft.rfft(data)
        magnitudes = np.abs(fft_res)
        return magnitudes