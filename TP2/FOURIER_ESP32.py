from machine import DAC, Pin
import math
import time

# Configuración del DAC (GPIO26 = DAC1)
dac = DAC(Pin(26))

# Parámetros de la onda
frecuencia_base = 1000  # Hz
muestras_por_ciclo = 100

def generar_onda_cuadrada_fourier(N, frecuencia):
    """
    Genera una onda cuadrada mediante la suma de armónicos impares
    hasta el N-ésimo, normalizada para el DAC.
    """
    T = 1 / frecuencia
    dt = T / muestras_por_ciclo
    onda = []
    for n in range(muestras_por_ciclo):
        t = n * dt
        valor = sum((1 / k) * math.sin(math.tau * k * frecuencia * t)
                    for k in range(1, N + 1, 2))
        onda.append(valor)

    # Normalización a rango 0-255 para DAC
    max_val = max(onda)
    min_val = min(onda)
    onda_normalizada = [
        int((val - min_val) / (max_val - min_val) * 255)
        for val in onda
    ]
    return onda_normalizada, dt

def graficar_onda_ascii(onda, alto=20, ancho=80):
    """
    Muestra una representación ASCII de la onda.
    """
    paso = max(1, len(onda) // ancho)
    onda_reducida = onda[::paso][:ancho]

    min_val = min(onda_reducida)
    max_val = max(onda_reducida)
    escala = (alto - 1) / (max_val - min_val) if max_val != min_val else 1
    niveles = [int((val - min_val) * escala) for val in onda_reducida]

    for nivel in reversed(range(alto)):
        linea = ''
        for punto in niveles:
            linea += '.' if punto == nivel else ' '
        print(linea)

while True:
    try:
        entrada = input("Ingresá un número impar de armónicos N (ej: 1,3,5...): ")
        if not entrada.strip().isdigit():
            print("Entrada inválida. Debe ser un número impar positivo.")
            continue
        N = int(entrada)
        if N % 2 == 0 or N <= 0:
            print("Por favor ingresá un valor impar positivo.")
            continue

        print(f"\nGenerando señal con N = {N} armónicos...")
        onda, dt = generar_onda_cuadrada_fourier(N, frecuencia_base)

        print("\nVista aproximada de la señal:")
        graficar_onda_ascii(onda)

        print("\nReproduciendo señal... (Ctrl+C para detener)\n")
        while True:
            for muestra in onda:
                dac.write(muestra)
                time.sleep_us(int(dt * 1_000_000))

    except KeyboardInterrupt:
        print("\nInterrumpido. Podés ingresar otro N.\n")
        continue
    except Exception as e:
        print("Error:", e)
