import os
from gtts import gTTS
import pygame

class AudioManager:
    def __init__(self):
        pygame.mixer.init()

    def reproducir_mensaje(self, mensaje):
        archivo_audio = os.path.join(os.path.dirname(__file__), fr"audios\{mensaje}.mp3")
        
        if not os.path.exists(archivo_audio):
            tts = gTTS(text=mensaje, lang='es', slow=False)
            try:
                tts.save(archivo_audio)
            except PermissionError:
                print(f"Error: No se pudo guardar el archivo {archivo_audio} debido a falta de permisos.")
                return
        
        pygame.mixer.music.load(archivo_audio)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload()

