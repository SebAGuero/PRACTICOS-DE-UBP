from machine import ADC, Pin, I2C
import ssd1306
import time
import math

# --- FFT iterativa radix-2 ---
def bit_reverse(x, bits):
    result = 0
    for i in range(bits):
        if x & (1 << i):
            result |= 1 << (bits - 1 - i)
    return result

def fft_iter(x):
    N = len(x)
    bits = int(math.log2(N))

    X = [0]*N
    for i in range(N):
        j = bit_reverse(i, bits)
        X[j] = complex(x[i], 0)

    size = 2
    while size <= N:
        half = size // 2
        phase_step = -2j * math.pi / size
        for i in range(0, N, size):
            for j in range(half):
                angle = j * phase_step
                twiddle = complex(math.cos(angle.imag), math.sin(angle.imag))
                a = X[i + j]
                b = X[i + j + half] * twiddle
                X[i + j] = a + b
                X[i + j + half] = a - b
        size *= 2
    return X

# --- Inicialización ---
i2c = I2C(0, scl=Pin(9), sda=Pin(8))
oled = ssd1306.SSD1306_I2C(128, 32, i2c)

adc = ADC(Pin(1))
adc.atten(ADC.ATTN_11DB)
adc.width(ADC.WIDTH_12BIT)

N_TOTAL = 512
ZOOM = 4
DELAY = 0.0008

# --- Carátula inicial ---
oled.fill(0)
oled.text("Osciloscopio", 10, 8)
oled.text("Micropython", 18, 18)
oled.show()
time.sleep(2)

oled.fill(0)
oled.text("Cargando...", 30, 12)
oled.show()
time.sleep(1)

# --- Loop principal ---
modo_fft = False
ultimo_cambio = time.ticks_ms()

while True:
    # Adquirir muestras
    raw = []
    for _ in range(N_TOTAL):
        raw.append(adc.read())
        time.sleep(DELAY)
     # Calcular promedio para eliminar componente DC
    promedio = sum(raw[:128]) / 128
    raw_dc = [v - promedio for v in raw[:128]]
    
     # Escalar y reducir cantidad de muestras para mostrar
    display_samples = []
    for i in range(0, len(raw), ZOOM):
        v = raw[i]
        y = 31 - int(v / 4095 * 31)  # escalar a 0–31
        display_samples.append(y)
    
    oled.fill(0)

    # Cambiar modo cada 1 segundo
    if time.ticks_diff(time.ticks_ms(), ultimo_cambio) > 3000:
        modo_fft = not modo_fft
        ultimo_cambio = time.ticks_ms()

    if not modo_fft:
        # Modo temporal
        #oled.text("Tiempo", 0, 0)
        display_samples = []
        for i in range(0, len(raw), ZOOM):
            y = 31 - int(raw[i] / 4095 * 31)
            display_samples.append(y)
        for x in range(min(128, len(display_samples))):
            oled.pixel(x, display_samples[x], 1)
        time.sleep(0.1)

    else:
        # Modo frecuencia (FFT)
        # oled.text("Frecuencia", 0, 0)

        fft_data = fft_iter(raw_dc)  # Usamos 128 puntos
        mag = [abs(c) for c in fft_data[:64]]  # Solo mitad (simétrica)
        max_mag = max(mag) if max(mag) != 0 else 1

        # Mostramos espectro simétrico
        for x in range(64):
            h = int(mag[x] / max_mag * 31)
            for y in range(h):
                # Parte derecha (original)
                oled.pixel(64 + x*4,     31 - y, 1)
                oled.pixel(64 + x*4 + 1, 31 - y, 1)
        
                # Parte izquierda (espejo)
                oled.pixel(63 - x*4,     31 - y, 1)
                oled.pixel(63 - x*4 - 1, 31 - y, 1)

    oled.show()
