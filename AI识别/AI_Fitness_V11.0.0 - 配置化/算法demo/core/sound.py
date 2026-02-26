import numpy as np
try: import pygame
except ImportError: pass
from core.config import AppConfig

class SoundManager:
    def __init__(self):
        self.sounds = {}
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self._gen_sounds()
        except: pass

    def _gen_wave(self, freq, dur, type='sine'):
        sr = 44100
        t = np.linspace(0, dur, int(sr*dur), False)
        if type == 'sine': w = np.sin(2*np.pi*freq*t)
        elif type == 'square': w = np.sign(np.sin(2*np.pi*freq*t))
        w *= np.linspace(1, 0, len(t)) * 0.5
        audio = (w * 32767).astype(np.int16)
        return pygame.sndarray.make_sound(np.column_stack((audio, audio)))

    def _gen_sounds(self):
        self.sounds['count'] = self._gen_wave(880, 0.1)
        self.sounds['error'] = self._gen_wave(150, 0.4, 'square')
        t = np.linspace(0, 0.6, int(44100*0.6), False)
        w = (np.sin(2*np.pi*523*t) + np.sin(2*np.pi*659*t) + np.sin(2*np.pi*784*t))/3
        w *= np.linspace(1, 0, len(t)) * 0.5
        audio = (w * 32767).astype(np.int16)
        self.sounds['success'] = pygame.sndarray.make_sound(np.column_stack((audio, audio)))

    def play(self, name):
        if name in self.sounds:
            try:
                self.sounds[name].set_volume(AppConfig.VOL)
                self.sounds[name].play()
            except: pass