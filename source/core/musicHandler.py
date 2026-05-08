import mutagen
import pygame.mixer as mixer
from collections import deque
import os
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation as animation
import numpy as np
import sounddevice as sd
import soundfile as sf
"""
TODO: Criar forma de gerenciar um multiProcessos com PID, com lock para não tocar mais de uma vez
E fazer com que renderize o waveform dentro do customTkinter com o matplotlib, usando o canvas do customTkinter para renderizar o gráfico, e não abrir uma janela separada
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
        
    def getTrackWaveform(self, filePath):
        try:
            data_info = sf.info(filePath)
            sr = data_info.samplerate
            plot_buffer = np.zeros(sr * 2)
            fig, ax = plt.subplots()
            line, = ax.plot(plot_buffer)
            ax.set_ylim(-1, 1)
            stream_file = sf.blocks(filePath, blocksize=CHUNK_SIZE, always_2d=True)

            def callback(outdata, frames, time, status):
                nonlocal plot_buffer
                try:
                    # Pega o próximo pedaço do arquivo
                    data = next(stream_file)
                    
                    # Envia para a saída de áudio, ajustando o tamanho se necessário
                    if len(data) < len(outdata):
                        outdata[:len(data)] = data
                        outdata[len(data):].fill(0)
                    else:
                        outdata[:] = data[:len(outdata)]
                    
                    # Atualiza o buffer do gráfico (pegando apenas o canal 0)
                    new_data = data[:, 0]
                    plot_buffer = np.roll(plot_buffer, -len(new_data))
                    plot_buffer[-len(new_data):] = new_data
                    
                except StopIteration:
                    outdata.fill(0)
                    raise sd.CallbackStop
                
            def update_plot(frame):
                line.set_ydata(plot_buffer)
                return line,

            # Abre o fluxo de saída
            with sd.OutputStream(samplerate=sr, channels=data_info.channels, callback=callback):
                ani = animation(fig, update_plot, interval=30, blit=True, cache_frame_data=False)
                plt.show()
        except Exception as e:
            print(f"Error generating waveform: {e}")

if __name__ == "__main__":
    filePath = "/home/guest/Área de trabalho/Projetos/Universidade/Python_Music_Player/source/musics/teste"
    handler = MusicHandler()
    handler.selectPlaylist(filePath)
    print(handler.playNext())
    handler.getTrackWaveform(handler.currentPlaying["filePath"])
    