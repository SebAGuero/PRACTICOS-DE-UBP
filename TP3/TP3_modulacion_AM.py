# -*- coding: utf-8 -*-
"""
Created on Fri May 16 00:16:19 2025

@author: Usuario01
"""

import numpy as np
import matplotlib.pyplot as plt
import soundfile as sf
import sounddevice as sd
from scipy.signal import butter, filtfilt

# Función para filtro pasa bajos
def filtro_pasabajos(data, fs, fc):
    b, a = butter(4, fc / (fs / 2), btype='low')  # Filtro de 4to orden
    return filtfilt(b, a, data)

# Función para calcular y devolver magnitud FFT y eje de frecuencias
def espectro(signal, fs):
    N = len(signal)
    freqs = np.fft.rfftfreq(N, 1/fs)
    spectrum = np.abs(np.fft.rfft(signal)) / N
    return freqs, spectrum

# 1. Leer archivo de audio
audio, fs = sf.read("C:/Users/Usuario01/tu_audio.ogg")  # Reemplazar con tu ruta

# 2. Convertir a mono si es estéreo
if len(audio.shape) == 2:
    audio = audio[:, 0]

# 3. Limitar a 15 segundos
duracion_segundos = 20
n_muestras = int(duracion_segundos * fs)
audio = audio[:n_muestras]

# 4. Normalizar
audio = audio / np.max(np.abs(audio))

# 5. Reproducir audio original
print("▶ Reproduciendo audio original...")
sd.play(audio, fs)
sd.wait()

# 6. Parámetros de modulación
fc = 10000  # frecuencia portadora (Hz)
m = 1       # índice de modulación

# 7. Vector de tiempo
t = np.arange(len(audio)) / fs

# 8. Generar portadora y señal AM
carrier = np.cos(2 * np.pi * fc * t)
am_signal = (1 + m * audio) * carrier

# 9. Normalizar señal AM
am_signal = am_signal / np.max(np.abs(am_signal))

# 10. Reproducir señal AM
print("▶ Reproduciendo señal AM...")
sd.play(am_signal, fs)
sd.wait()

# 11. Demodulación: detección de envolvente
envolvente = np.abs(am_signal)

# 12. Filtro pasa bajos (FPB) con cutoff a 2 kHz
fc_lp = 2000  # Hz
audio_recuperado = filtro_pasabajos(envolvente, fs, fc_lp)

# 13. Normalizar señal demodulada
audio_recuperado = audio_recuperado / np.max(np.abs(audio_recuperado))

# 14. Reproducir señal demodulada
print("▶ Reproduciendo señal demodulada...")
sd.play(audio_recuperado, fs)
sd.wait()


# 15. Graficar señales (primeros 20 s)
win_len = int(20 * fs)

plt.figure(figsize=(12, 10))

plt.subplot(4, 1, 1)
plt.plot(t[:win_len], audio[:win_len], color='blue')
plt.title('Señal Original (Modulante)')
plt.ylabel('Amplitud')
plt.grid(True)

plt.subplot(4, 1, 2)
plt.plot(t[:win_len], carrier[:win_len], color='orange')
plt.title('Portadora (10 kHz)')
plt.ylabel('Amplitud')
plt.grid(True)

plt.subplot(4, 1, 3)
plt.plot(t[:win_len], am_signal[:win_len], color='green')
plt.title('Señal AM')
plt.ylabel('Amplitud')
plt.grid(True)

plt.subplot(4, 1, 4)
plt.plot(t[:win_len], audio_recuperado[:win_len], color='red')
plt.title('Señal Demodulada (FPB 2 kHz)')
plt.xlabel('Tiempo [s]')
plt.ylabel('Amplitud')
plt.grid(True)

plt.tight_layout()
plt.show()

# 16. Gráficas espectrales
freq_audio, spec_audio = espectro(audio, fs)
freq_carrier, spec_carrier = espectro(carrier, fs)
freq_am, spec_am = espectro(am_signal, fs)
freq_demod, spec_demod = espectro(audio_recuperado, fs)

plt.figure(figsize=(12, 10))

plt.subplot(4, 1, 1)
plt.plot(freq_audio, spec_audio, color='blue')
plt.title('Espectro - Señal Original')
plt.xlim(0, 4000)
plt.ylabel('Magnitud')
plt.grid(True)

plt.subplot(4, 1, 2)
plt.plot(freq_carrier, spec_carrier, color='orange')
plt.title('Espectro - Portadora')
plt.xlim(0, 10000)
plt.ylabel('Magnitud')
plt.grid(True)

plt.subplot(4, 1, 3)
plt.plot(freq_am, spec_am*10, color='green')
plt.title('Espectro - Señal AM')
plt.xlim(0, 10000)
plt.ylim(0,0.03)
plt.ylabel('Magnitud')
plt.grid(True)

plt.subplot(4, 1, 4)
plt.plot(freq_demod, spec_demod, color='red')
plt.title('Espectro - Señal Demodulada')
plt.xlim(0, 4000)
plt.ylim(0,0.006)
plt.xlabel('Frecuencia [Hz]')
plt.ylabel('Magnitud')
plt.grid(True)


plt.tight_layout()
plt.show()
