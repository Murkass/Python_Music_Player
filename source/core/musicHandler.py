import mutagen
import pygame.mixer as mixer
from collections import deque
import os

"""
TODO: adicionar uma forma de ler FLAC, e tentar arrumar a exibição do waveform das musicas, 
e fazer colorir a parte que ja foi tocada.

"""
class MusicHandler:
    def __init__(self):
        self.currentPlaying = None
        self.playingQueue = deque()
        self.historic = deque(maxlen=50)
        self.paused = False
        mixer.init()

    def addToQueue(self, filePath):
        try:
            audio = mutagen.File(filePath)
            title = audio.get("TIT2", "Unknown Title")
            artist = audio.get("TPE1", "Unknown Artist")
            time = int(audio.info.length)
            minutes = time // 60
            seconds = time % 60
            formatted_time = f"{minutes}:{seconds:02d}"
            self.playingQueue.append({
                "filePath": filePath,
                "title": title,
                "artist": artist,
                "time": formatted_time
            })
        except Exception as e:
            print(f"Error adding to queue: {e}")

    def clearQueue(self):
        self.playingQueue.clear()
        self.historic.clear()
        self.currentPlaying = None
        mixer.music.stop()

    def selectPlaylist(self, playlistPath):
        self.clearQueue()
        musics = [f for f in os.listdir(playlistPath) if f.endswith(('.mp3', '.wav', '.ogg', '.flac'))]
        for music in musics:
            self.addToQueue(os.path.join(playlistPath, music))

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
        except Exception as e:
            print(f"Error playing next track: {e}")
        else:
            self.currentPlaying = None


    def playPrevious(self):
        try:
            if self.historic:
                self.playingQueue.appendleft(self.currentPlaying) if self.currentPlaying else None
                self.currentPlaying = self.historic.popleft()
                mixer.music.load(self.currentPlaying["filePath"])
                mixer.music.play()
        except Exception as e:
            print(f"Error playing previous track: {e}")
        else:
            return

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
        