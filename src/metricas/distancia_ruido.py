import numpy as np


def distancia_ruido(C_original, C_ruido):
    """
    Calcula la distancia normalizada entre la matriz original C
    y la matriz perturbada C_ruido.

    Devuelve:
        D(C, C_ruido) / n(n-1)
    """
    n = C_original.shape[0]
    return float(np.sum(np.abs(C_original - C_ruido)) / (n * (n - 1)))