"""
Estrategias de agregación de ruido sobre scores latentes.

Este módulo implementa las estrategias de perturbación aplicadas sobre los scores latentes.
La idea parte de la contrucción de scores latentes a partir de la matriz de precedencias. Estos scores se perturban añadiendo ruido de Laplace y finalmente se reconstruye una nueva matriz de precedencias a partir de los scores perturbados.
"""

import numpy as np
from scipy.stats import norm

from data.preflib_to_C import validar_C


def estimar_scores(C):
    """
    Estima un score para cada ítem sumando su fila en la matriz C.
    Se hace mediante un suma por filas de la matriz de precedencias. Un score alto indica que el ítem es preferido frente a muchos otros, mientras que un score bajo indica lo contrario.
    Después se normalizan los scores para que el ruido afecte de forma más estable.
    """
    scores = np.sum(C, axis=1)
    desviacion = scores.std()

    if desviacion == 0:
        return np.zeros_like(scores, dtype=float)

    return (scores - scores.mean()) / desviacion


def funcion_logistica(x):
    """
    Función logística:
        sigma(x) = 1 / (1 + exp(-x))
    """
    return 1.0 / (1.0 + np.exp(-x))


def funcion_probit(x):
    """
    Función probit:
        sigma(x) = Phi(x)
    """
    return norm.cdf(x)


def agregar_ruido_scores(scores, b, rng):
    """
    Añade ruido de Laplace a cada score latente.
    El parámetro b controla la intensidad del ruido
    """
    ruido = rng.laplace(loc=0.0, scale=b, size=scores.shape)
    return scores + ruido


def reconstruir_matriz_desde_scores(scores, funcion_sigma):
    """
    Reconstruye una matriz de precedencias a partir de los scores perturbados.
    Para cada par de ítems se compara la diferencia entre sus scores. El resultado se transforma en un valor entre 0 y 1 mediante la función elegida.
    """
    n = len(scores)
    C_ruido = np.full((n, n), 0.5, dtype=float)

    for i in range(n):
        for j in range(i + 1, n):
            valor = float(funcion_sigma(scores[i] - scores[j]))

            C_ruido[i, j] = valor
            C_ruido[j, i] = 1.0 - valor

    np.fill_diagonal(C_ruido, 0.5)

    return validar_C(C_ruido)


def seleccionar_funcion_sigma(tecnica):
    if tecnica == "logistic":
        return funcion_logistica

    if tecnica == "probit":
        return funcion_probit

    raise ValueError("tecnica debe ser: logistic o probit")


def aplicar_ruido_scores(C, b, rng, tecnica):
    """
    Aplica ruido sobre scores latentes y devuelve la matriz C perturbada.
    Primero se estiman scores a partir de la matriz original, después se les añade ruido y finalmente se reconstruye una nueva matriz de precedencias.
    """
    C = validar_C(C)

    scores = estimar_scores(C)
    scores_ruido = agregar_ruido_scores(scores, b, rng)
    funcion_sigma = seleccionar_funcion_sigma(tecnica)

    return reconstruir_matriz_desde_scores(scores_ruido, funcion_sigma)