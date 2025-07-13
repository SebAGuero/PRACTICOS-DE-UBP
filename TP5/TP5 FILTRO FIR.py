#Universidad Blas Pascal
#Procesamiento Digital de Senales
#Filtro FIR Orden 20, f=100Hz

from machine import Pin, I2C
import ssd1306
import math
import time
from ssd1306 import SSD1306_I2C

# ---------- OLED setup ----------
# Inicializamos la comunicación I2C para el OLED.
# Usamos los pines GPIO 22 (SCL) y 21 (SDA), cambiar si usás otros pines en el microcontrolador.
i2c = I2C(0, scl=Pin(22), sda=Pin(21))  
oled = ssd1306.SSD1306_I2C(128, 32, i2c)  # Creamos objeto para controlar OLED 128x64

# ---------- Coeficientes FIR ----------
# FIR: filtro digital de respuesta finita (Finite Impulse Response)
# Orden 20, por eso hay 21 coeficientes (se cuenta desde b0 hasta b20)
b = [-0.00000062, -0.00212227, -0.00632535, -0.01161181, -0.01235466,
      0.00000000,  0.03177450,  0.08143591,  0.13749378,  0.18212549,
      0.19916883,  0.18212549,  0.13749378,  0.08143591,  0.03177450,
      0.00000000, -0.01235466, -0.01161181, -0.00632535, -0.00212227,
     -0.00000062]

# Características del filtro:
# - Tipo: FIR no recursivo (no usa realimentación)
# - Filtro pasabajos de fase lineal
# - Orden: 20 (21 coeficientes)
# - Ventana: Hamming (para suavizar los coeficientes y controlar el lobulo lateral)
# - Frecuencia de corte (-3dB): 100 Hz
# - Aproximación: no aplica (no es un filtro IIR ni aproximado)

# Ecuación en diferencias:
# y[n] = sumatoria de b[k]*x[n-k] para k=0 hasta 20
# (Aquí se expande con todos los coeficientes para que vean cómo afecta cada muestra pasada)

#y[n] = -0.00000062x[n] -0.00212227x[n-1] -0.00632535x[n-2] -0.01161181x[n-3] -0.01235466x[n-4] 0.0x[n-5] +0.03177450x[n-6] +0.08143591x[n-7]+
#       +0.13749378x[n-8] +0.18212549x[n-9] +0.19916883x[n-10] +0.18212549x[n-11] +0.13749378x[n-12] +0.08143591x[n-13] +0.03177450x[n-14]+
#       +0.0x[n-15] -0.01235466x[n-16] -0.01161181x[n-17] -0.00632535x[n-18] -0.00212227x[n-19] -0.00000062x[n-20]


# ---------- Señal de entrada simulada ----------
fs = 5000  # Frecuencia de muestreo en Hz
# Nota: fs=5000Hz permite medir señales hasta 2500Hz según Nyquist (pero el filtro corta a 100Hz)
N = 256    # Número de muestras a procesar
t = [i / fs for i in range(N)]  # Vector de tiempos, de 0 a (N-1)/fs segundos

# Señal compuesta por varias frecuencias (componentes espectrales)
# Se suman senoidales de diferentes frecuencias y amplitudes:
# 10, 20, 80, 120, 550, 800, 900, 1000 Hz
# La idea es que el filtro pasabajos atenúe las frecuencias altas (mayores a 100 Hz)
x = [
    2.0 * math.sin(2 * math.pi * 10 * ti)   +  # frecuencia 10 Hz, amplitud 2
    1.0 * math.sin(2 * math.pi * 60 * ti)   +  # etc...
    1.0 * math.sin(2 * math.pi * 100 * ti)  +
    0.9 * math.sin(2 * math.pi * 550 * ti)  +
    0.9 * math.sin(2 * math.pi * 800 * ti)  +
    0.9 * math.sin(2 * math.pi * 900 * ti)  +
    0.9 * math.sin(2 * math.pi * 1000 * ti)
    for ti in t
]



# ---------- Filtrado FIR ----------
M = len(b)      #Mi longitud va a ser la longitud de todos los coeficientes previamente cargados en mis b_k
x_pad = [0] * M #sirve para inicializar una "ventana deslizante" de longitud M, que en este caso es la cantidad de
                #coeficientes del filtro FIR (o sea, el orden del filtro + 1).
y = []         #por defecto vacio, aca se guardara la salida del filtro que calculmos a cada instante


#¿Qué representa?
#En un filtro FIR, para calcular cada salida 𝑦[𝑛], necesitás una cierta cantidad de muestras pasadas de la entrada 𝑥[𝑛],𝑥[𝑛−1],...,𝑥[𝑛−𝑀+1].
#Esto se llama ventana o buffer de muestras pasadas.

#¿Por qué se hace así?
#[0] * M crea una lista con M ceros:

#M = 21
#x_pad = [0] * 21  # => [0, 0, 0, ..., 0]

#Esto representa que al comienzo del filtrado, no hay muestras anteriores, así que arrancás con ceros
#(como si la señal anterior no existiera). A esto se le llama relleno con ceros o **zero-padding**.

#¿Qué pasa después?
#Cada vez que llega una nueva muestra 𝑥[𝑛], actualizás el buffer así:
#x_pad = [x[n]] + x_pad[:-1]

#Esto hace lo siguiente:
#                       - Mete la nueva muestra al principio de la lista.
#                       - Quita la última muestra (la más vieja).

#Así siempre tenés un buffer actualizado con las últimas M muestras para aplicar:
#      M−1
#y[n]= ∑  b[k]⋅x[n−k]
#      k=0

for n in range(len(x)):
    x_pad = [x[n]] + x_pad[:-1]  # Ventana deslizante
    yn = 0
    for k in range(M):
        yn += b[k] * x_pad[k]
    y.append(yn)
#-----------------------------------------------------

# ---------- DFT (solo magnitud) ----------
def dft(signal):
    N = len(signal)
    mean = sum(signal) / N
    signal = [s - mean for s in signal]  # Centrado
    spectrum = []
    for k in range(N // 2):
        re = 0
        im = 0
        for n in range(N):
            angle = -2 * math.pi * k * n / N
            re += signal[n] * math.cos(angle)
            im += signal[n] * math.sin(angle)
        mag = math.sqrt(re ** 2 + im ** 2)
        spectrum.append(mag)
    return spectrum

# ---------- Mostrar en OLED ----------
def plot_spectrum(spectrum):
    oled.fill(0)
    max_val = max(spectrum)
    if max_val == 0:
        max_val = 1

    for i in range(min(len(spectrum), 64)):  
        h = int((spectrum[i] / max_val) * 31)
        x_pos = 2 * i
        oled.line(x_pos, 31, x_pos, 31 - h, 1)
        oled.line(x_pos + 1, 31, x_pos + 1, 31 - h, 1)
    oled.show()


#ZOOM DE ANCHO 0-200HZ/----------------------------
def plot_spectrum_zoom(spectrum, zoom_bins=12):
    oled.fill(0)
    max_val = max(spectrum[:zoom_bins])
    if max_val == 0:
        max_val = 1  # evitar división por cero

    ancho_px = 128  # Ancho del OLED
    escala_x = ancho_px // zoom_bins

    for i in range(zoom_bins):
        h = int((spectrum[i] / max_val) * 31)  # altura en 0-31
        x_pos = i * escala_x
        # dibujar barra delgada o ancha (puede ajustarse)
        oled.line(x_pos, 31, x_pos, 31 - h, 1)
        oled.line(x_pos + 1, 31, x_pos + 1, 31 - h, 1)

    #oled.text("Zoom 0-200Hz", 0, 0, 1)
    oled.show()



# ---------- Interfaz serial ----------
def esperar_comando():
    print("\nComandos disponibles:")
    print(" 1 - Ver espectro señal original")
    print(" 2 - Ver espectro señal filtrada")
    print(" 3 - Ver diagrama magnitud del filtro FIR")
    print(" 4 - Ver diagrama fase del filtro FIR")
    print(" 5 - Ver espectro zoom (0-200 Hz)")
    print(" q - Salir (reset manual)")
    cmd = input(">> ").strip()
    return cmd

# ---------------------------------------
# --- Agrego para opción 3 y 4 (Magnitud y Fase FIR)
# ---------------------------------------


def dft_complex(signal, N):
    """Calcula DFT y devuelve lista de valores complejos para N puntos"""
    result = []
    L = len(signal)
    for k in range(N):
        re = 0
        im = 0
        for n in range(L):
            angle = -2 * math.pi * k * n / N
            re += signal[n] * math.cos(angle)
            im += signal[n] * math.sin(angle)
        result.append(complex(re, im))
    return result

def magnitud(dft_vals):
    return [abs(c) for c in dft_vals]

def fase(dft_vals):
    # Fase en grados, entre -180 y 180
    return [math.degrees(math.atan2(c.imag, c.real)) for c in dft_vals]

def plot_magnitude_phase(oled_32, mag, ph, show_phase=False):
    oled_32.fill(0)
    max_mag = max(mag) if mag else 1
    # Normalizamos magnitud a 0-31 pix (alto OLED 32 px)
    mag_norm = [int((m / max_mag) * 31) for m in mag]

    # Para fase normalizamos desde -180 a 180 grados a 0-31 pix
    ph_norm = [int(((p + 180) / 360) * 31) for p in ph]

    length = min(len(mag_norm), 128)  # max ancho OLED

    for x in range(length):
        if show_phase:
            y = 31 - ph_norm[x]  # invertido para que 0 esté abajo
        else:
            y = 31 - mag_norm[x]
        oled_32.pixel(x, y, 1)

    # Título (texto muy pequeño, si oled lo permite)
    oled_32.text("Fs" if show_phase else "Mg", 0, 0, 1)
    oled_32.show()

def mostrar_magnitud():
    N_fft = 128
    dft_vals = dft_complex(b, N_fft)
    mag = magnitud(dft_vals)
    ph = fase(dft_vals)  # No se usa acá pero la calculo para consistencia
    plot_magnitude_phase(oled, mag, ph, show_phase=False)
    time.sleep(10)  # mostrar 10 segundos o el tiempo que quieras

def mostrar_fase():
    N_fft = 128
    dft_vals = dft_complex(b, N_fft)
    mag = magnitud(dft_vals)  # No se usa acá pero la calculo para consistencia
    ph = fase(dft_vals)
    plot_magnitude_phase(oled, mag, ph, show_phase=True)
    time.sleep(10)  # mostrar 10 segundos o el tiempo que quieras


# ---------- Loop principal ----------
while True:
    cmd = esperar_comando()
    if cmd == "1":
        print("Mostrando espectro de señal original (x[n])...")
        spec = dft(x)
        plot_spectrum(spec)
    elif cmd == "2":
        print("Mostrando espectro de señal filtrada (y[n])...")
        spec = dft(y)
        plot_spectrum(spec)
    elif cmd == "3":
        print("Mostrando diagrama de magnitud del filtro FIR...")
        mostrar_magnitud()
    elif cmd == "4":
        print("Mostrando diagrama de fase del filtro FIR...")
        mostrar_fase()
    elif cmd == "q":
        print("Fin del programa. Reiniciá el ESP32 si querés reiniciar.")
        break
    elif cmd == "5":
        print("Mostrando espectro de bajas frecuencias (zoom)...")
        spec = dft(x)
        plot_spectrum_zoom(spec, zoom_bins=12)
    else:
        print("Comando no reconocido. Ingresá 1, 2, 3, 4 o q.")
#----------------------------------------------------------------FIN------------------------------------------------------------------------