"""
Métricas para evaluar la sensibilidad al ruido de los métodos de agregación.
"""
import numpy as np

from metricas.perdida_calidad import construir_matriz_bucket


def distancia_matrices(C_original, C_ruido):
    """
    Distancia normalizada entre dos matrices de precedencias.
    """
    C_original = np.asarray(C_original, dtype=float)
    C_ruido = np.asarray(C_ruido, dtype=float)

    if C_original.shape != C_ruido.shape:
        raise ValueError("Las matrices deben tener la misma dimensión")

    n = C_original.shape[0]

    if n <= 1:
        return 0.0

    mascara = ~np.eye(n, dtype=bool) # Solo consideramos los pares de alternativas distintas
    distancia = np.sum(np.abs(C_original[mascara] - C_ruido[mascara]))

    return float(distancia / (n * (n - 1)))


def distancia_bucket_orders(buckets_original, buckets_ruido, n):
    """
    Distancia normalizada entre dos bucket orders.

    Los bucket orders se transforman en sus matrices B asociadas
    para poder comparar sus relaciones por pares.
    """
    if n <= 1:
        return 0.0

    B_original = construir_matriz_bucket(buckets_original, n)
    B_ruido = construir_matriz_bucket(buckets_ruido, n)

    return distancia_matrices(B_original, B_ruido)


def sensibilidad_ruido(distancia_entrada, distancia_salida):
    """
    Calcula la sensibilidad del resultado frente al ruido:

        S = distancia_salida / distancia_entrada

    Si no hay perturbación en la entrada, la sensibilidad no
    está definida y se devuelve NaN.
    """
    if distancia_entrada == 0:
        if distancia_salida == 0:
            return 0.0
        return float("nan")

    return float(distancia_salida / distancia_entrada)
