import numpy as np

def construir_matriz_bucket(buckets, n):
    """
    Convierte un bucket order en su matriz B asociada.

    Si u precede a v, B[u,v] = 1.
    Si v precede a u, B[u,v] = 0.
    Si están empatados, B[u,v] = 0.5.
    """
    B = np.full((n, n), 0.5, dtype=float)

    posiciones = {}

    for indice_bucket, bucket in enumerate(buckets):
        for item in bucket:
            posiciones[item] = indice_bucket

    for u in range(1, n + 1):
        for v in range(1, n + 1):
            if posiciones[u] < posiciones[v]:
                B[u - 1, v - 1] = 1.0
            elif posiciones[u] > posiciones[v]:
                B[u - 1, v - 1] = 0.0
            else:
                B[u - 1, v - 1] = 0.5

    return B


def distancia_bucket_C(buckets, C):
    """
    Calcula la distancia entre un bucket order y una matriz de precedencias C.
    """
    B = construir_matriz_bucket(buckets, C.shape[0])
    return float(np.sum(np.abs(B - C)))


def perdida_calidad(buckets_original, buckets_ruido, C_original):
    """
    Calcula cuánto empeora el consenso con ruido respecto al consenso original.

    Se evalúan ambos bucket orders sobre la matriz original C.
    """
    distancia_original = distancia_bucket_C(buckets_original, C_original)
    distancia_ruido = distancia_bucket_C(buckets_ruido, C_original)

    return float(distancia_ruido - distancia_original)