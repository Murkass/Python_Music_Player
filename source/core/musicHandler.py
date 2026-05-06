import mutagen
import pygame.mixer

class MusicHandler:
    def __init__(self):
        self.currentPlaying = None
        self.playingQueue = []
        pygame.mixer.init()

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

    def playNext(self):
        if self.playingQueue:
            self.currentPlaying = self.playingQueue.pop(0)
            pygame.mixer.music.load(self.currentPlaying["filePath"])
            pygame.mixer.music.play()
        else:
            self.currentPlaying = None