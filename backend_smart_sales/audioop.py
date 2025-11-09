"""
Módulo ficticio 'audioop' para compatibilidad con Python 3.13.
Evita errores de importación en librerías como speech_recognition o pydub.
No realiza procesamiento real de audio.
"""

def getsample(audio, width, index):
    return 0

def add(a, b, width):
    return a

def mul(audio, width, factor):
    return audio

def avg(audio, width):
    return 0

def maxpp(audio, width):
    return 0

def rms(audio, width):
    return 0

def avgpp(audio, width):
    return 0

def cross(audio1, audio2, width):
    return 0

def lin2lin(audio, width_from, width_to):
    return audio

def tostereo(audio, width, lfactor, rfactor):
    return audio

def tomono(audio, width, lfactor, rfactor):
    return audio
