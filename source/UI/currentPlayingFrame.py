import customtkinter as ctk
import math
import numpy as np
from source.core.musicHandler import MusicHandler


class CurrentPlayingFrame(ctk.CTkFrame):
    def __init__(self, master, musicHandler: MusicHandler):
        super().__init__(master)
        self.master = master
        self.handler = musicHandler

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=0)
        self.columnconfigure((0, 1, 2), weight=1)

        self.track_label = ctk.CTkLabel(self, text="Nenhuma música tocando", anchor="w")
        self.track_label.grid(row=0, column=0, padx=10, pady=5, sticky="we")

        cControlFrame = ctk.CTkFrame(self, fg_color="transparent")
        cControlFrame.grid(row=0, column=1, padx=10, pady=5)

        self.prev_btn = ctk.CTkButton(cControlFrame, text="<-", width=40, command=self._prev)
        self.prev_btn.pack(side="left", padx=5)
        self.play_btn = ctk.CTkButton(cControlFrame, text="Play", width=40, command=self._toggle_play_pause)
        self.play_btn.pack(side="left", padx=5)
        self.next_btn = ctk.CTkButton(cControlFrame, text="->", width=40, command=self._next)
        self.next_btn.pack(side="left", padx=5)

        self.placeholder = ctk.CTkLabel(self, text="", anchor="e")
        self.placeholder.grid(row=0, column=2, padx=10, pady=5, sticky="we")

        # Canvas onde ficará o analisador/espectrograma e a barra de progresso
        self.canvas = ctk.CTkCanvas(self, height=120, highlightthickness=0, bg=f"{self.cget("fg_color")[1]}")
        self.canvas.grid(row=1, column=0, columnspan=3, sticky="we", padx=10, pady=5)

        # Número de barras (conforme solicitado)
        self.num_bars = 22
        self.bar_ids = []
        for _ in range(self.num_bars):
            # cria linhas verticais que serão renderizadas com capstyle 'round' (barras arredondadas)
            bid = self.canvas.create_line(0, 0, 0, 0, fill="#263244", width=3, capstyle='round')
            self.bar_ids.append(bid)

        # cores e parâmetros de renderização (fora do loop)
        self.filled_color = "#1F6FEB"  # azul escuro para preenchimento
        self.unfilled_color = "#263244"  # cinza-azulado escuro para não-preenchido
        self.height_scale = 0.55  # reduz a altura das barras
        self.gap = 8  # espaçamento entre barras
        # buffer para suavização entre frames
        self.prev_heights = np.zeros(self.num_bars, dtype=float)
        self.smoothing_alpha = 0.35

        self.after(100, self._update_ui)

    def _prev(self):
        try:
            self.handler.playPrevious()
        except Exception as e:
            print(f"Error previous: {e}")

    def _next(self):
        try:
            self.handler.playNext()
        except Exception as e:
            print(f"Error next: {e}")

    def _toggle_play_pause(self):
        try:
            self.handler.playPause()
        except Exception as e:
            print(f"Error play/pause: {e}")

    def _update_ui(self):
        info = None
        try:
            info = self.handler.getCurrentTrackInfo()
        except Exception as e:
            print(f"Error getting current track info: {e}")

        total_seconds = 0
        if info:
            self.track_label.configure(text=f"{info.get('title','Unknown')} - {info.get('artist','Unknown')}")
            # parse total time "M:SS"
            t = info.get('time', '0:00')
            try:
                parts = t.split(":")
                mins = int(parts[0])
                secs = int(parts[1]) if len(parts) > 1 else 0
                total_seconds = mins * 60 + secs
            except Exception:
                total_seconds = 0
            try:
                paused = getattr(self.handler, 'paused', False)
                self.play_btn.configure(text="Play" if paused else "Pause")
            except Exception:
                pass
        else:
            self.track_label.configure(text="Nenhuma música tocando")
            self.play_btn.configure(text="Play")

        # posição atual em segundos (pede ao handler)
        try:
            current_pos = getattr(self.handler, 'getCurrentPosition', lambda: 0)()
        except Exception:
            current_pos = 0

        percent = 0.0
        if total_seconds > 0:
            percent = min(1.0, current_pos / total_seconds)

        filled_bars = int(math.floor(self.num_bars * percent))

        # Tenta obter dados de espectro do handler para gerar alturas (centralizadas e espelhadas)
        heights = np.zeros(self.num_bars, dtype=float)
        try:
            file_path = None
            if getattr(self.handler, 'currentPlaying', None):
                file_path = self.handler.currentPlaying.get('filePath')
            if file_path and getattr(self.handler, 'getSpectrumData', None):
                mags = self.handler.getSpectrumData(file_path)
                if mags is not None and len(mags) >= 2:
                    mags = np.array(mags)
                    # Ignorar DC para evitar dominação por offset
                    mags = mags[1:]
                    n = len(mags)
                    half_count = math.ceil(self.num_bars / 2)

                    # gerar bordas linearmente espaçadas (mais simples e previsível)
                    edges = np.unique(np.linspace(1, n, num=half_count + 1).astype(int))

                    # garantir bordas válidas
                    if edges[0] < 1:
                        edges[0] = 1
                    if edges[-1] < n:
                        edges = np.append(edges, n)
                    if len(edges) < half_count + 1:
                        edges = np.linspace(1, n, num=half_count + 1).astype(int)

                    vals_half = []
                    for i in range(len(edges) - 1):
                        s = edges[i] - 1
                        e = edges[i + 1] - 1
                        if s < 0:
                            s = 0
                        if e <= s:
                            seg = mags[s:s + 1]
                        else:
                            seg = mags[s:e]
                        if seg.size:
                            # use RMS for stability
                            vals_half.append(np.sqrt(np.mean(np.square(seg))))
                        else:
                            vals_half.append(0.0)

                    vals_half = np.array(vals_half, dtype=float)
                    if vals_half.size == 0:
                        vals_half = np.zeros(half_count)

                    # dynamic range compression (log) to reduce dominance of very large bins
                    vals_half = np.log1p(vals_half)
                    maxv = np.max(vals_half) if np.max(vals_half) > 0 else 1.0
                    half_norm = vals_half / maxv

                    # boost higher-frequency bins (outer bars) to make extremes more visible
                    freq_boost = getattr(self, 'freq_boost', 1.8)
                    boost_curve = np.linspace(1.0, freq_boost, num=len(half_norm))
                    half_norm = half_norm * boost_curve

                    # gamma correction to lift lower values (gamma < 1 boosts small numbers)
                    gamma = getattr(self, 'gamma', 0.6)
                    half_norm = np.power(half_norm, gamma, where=(half_norm>=0))

                    # renormalize after boosts
                    if np.max(half_norm) > 0:
                        half_norm = half_norm / np.max(half_norm)

                    mid = self.num_bars // 2
                    # mirror half_norm to both sides around center
                    if self.num_bars % 2 == 1:
                        for i, v in enumerate(half_norm):
                            if i == 0:
                                heights[mid] = v
                            else:
                                left = mid - i
                                right = mid + i
                                if 0 <= left < self.num_bars:
                                    heights[left] = v
                                if 0 <= right < self.num_bars:
                                    heights[right] = v
                    else:
                        for i, v in enumerate(half_norm):
                            left = mid - 1 - i
                            right = mid + i
                            if 0 <= left < self.num_bars:
                                heights[left] = v
                            if 0 <= right < self.num_bars:
                                heights[right] = v

                    # spatial smoothing to spread energy to neighbors
                    try:
                        kernel = np.array([0.25, 0.5, 0.25])
                        heights = np.convolve(heights, kernel, mode='same')
                    except Exception:
                        pass

                    # temporal smoothing to reduce jitter
                    new_h = heights.copy()
                    smoothed = (1.0 - self.smoothing_alpha) * self.prev_heights + self.smoothing_alpha * new_h
                    heights = smoothed
                    self.prev_heights = heights
        except Exception:
            pass

        # Atualiza barras no canvas usando linhas com capstyle 'round'
        width = self.canvas.winfo_width() or self.winfo_width() or 400
        height = self.canvas.winfo_height() or 100
        gap = getattr(self, 'gap', 3)
        bar_w = max(2, (width - (self.num_bars + 1) * gap) / self.num_bars)
        for i, bid in enumerate(self.bar_ids):
            x_center = gap + i * (bar_w + gap) + (bar_w / 2)
            h = int(heights[i] * height * getattr(self, 'height_scale', 0.55))
            y1 = max(0, height - h)
            y2 = height - 1
            try:
                self.canvas.coords(bid, x_center, y1, x_center, y2)
                color = self.filled_color if i < filled_bars else self.unfilled_color
                # largura da linha controla a espessura da barra; capstyle='round' deixa as extremidades arredondadas
                actual_line_width = max(1.0, bar_w * 1.2)
                self.canvas.itemconfig(bid, fill=color, width=actual_line_width)
            except Exception:
                pass

        self.after(100, self._update_ui)

    
