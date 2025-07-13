from machine import Pin, I2C
import ssd1306
import math
import time

# Configuración I2C y OLED
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
oled = ssd1306.SSD1306_I2C(128, 32, i2c)

fs = 10000  # Frecuencia de muestreo: 10 kHz
N = 256     # Cantidad de muestras

# Parámetros señal AM
f_portadora = 1000  # 1 kHz
f_modulante = 100   # 100 Hz
indice_modulacion = 1.5

def generar_am():
    señal = []
    for n in range(N):
        t = n / fs
        modulante = math.cos(2 * math.pi * f_modulante * t)
        portadora = math.cos(2 * math.pi * f_portadora * t)
        val = (1 + indice_modulacion * modulante) * portadora
        señal.append(val)
    return señal

def fft(x):
    N = len(x)
    if N <= 1:
        return x
    even = fft(x[0::2])
    odd = fft(x[1::2])
    T = [complex(math.cos(-2 * math.pi * k / N), math.sin(-2 * math.pi * k / N)) * odd[k] for k in range(N // 2)]
    return [even[k] + T[k] for k in range(N // 2)] + [even[k] - T[k] for k in range(N // 2)]

def mostrar_onda(señal):
    oled.fill(0)
    step = N // 128  # 256 muestras en 128 píxeles → mostrar cada 2da muestra
    for x in range(127):
        y1 = int((señal[x * step] + 1.5) * (31 / 3))  # Normalizar a pantalla
        y2 = int((señal[(x + 1) * step] + 1.5) * (31 / 3))
        oled.line(x, 31 - y1, x + 1, 31 - y2, 1)
    oled.show()

def mostrar_espectro(señal):
    oled.fill(0)
    resultado = fft(señal)
    mag = [abs(c) for c in resultado[:N // 2]]
    max_mag = max(mag) if mag else 1

    bins_a_mostrar = 64  # número de barras para que haya separación
    ancho_oled = 128
    espacio_total = ancho_oled // bins_a_mostrar  # 2 px por barra + espacio

    bins_por_barra = int(bins_a_mostrar / bins_a_mostrar)  # 1 bin por barra

    for i in range(bins_a_mostrar):
        start = i  # 1 bin por barra
        val = mag[start] if start < len(mag) else 0
        alto = max(1, int((val / max_mag) * 31))
        x = i * espacio_total
        # Dibujar barra de ancho 1 px, dejando 1 px vacío después
        oled.fill_rect(x, 31 - alto, 1, alto, 1)

    oled.show()




modo = 0
while True:
    señal = generar_am()
    if modo == 0:
        mostrar_onda(señal)
    else:
        mostrar_espectro(señal)
    modo = 1 - modo
    time.sleep(1)