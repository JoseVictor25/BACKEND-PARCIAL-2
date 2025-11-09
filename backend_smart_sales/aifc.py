"""
Módulo ficticio 'aifc' para compatibilidad con SpeechRecognition en Python 3.13.
Este stub evita el error de importación, ya que SpeechRecognition no usa aifc directamente
salvo para detección de formatos no WAV/FLAC.
"""

def open(file, mode=None):
    raise NotImplementedError("El módulo 'aifc' no está soportado en Python 3.13.")
