import numpy as np

from data.preflib_to_C import validar_C


PROBABILIDAD_ALEATORIA = 0.30
UMBRAL_CERCA_EMPATE = 0.10


def perturbar_matriz_laplace(C, b, criterio, rng):
    """
    Genera una nueva matriz de precedencias añadiendo ruido de Laplace.
    El parámetro b controla la intensidad del ruido. El criterio indica
    qué pares de elementos se perturban y cuáles se dejan igual.
    """

    C = validar_C(C)
    n = C.shape[0]
    C_ruido = C.copy()

    for i in range(n):
        for j in range(i + 1, n):
            if criterio(i, j, C):
                ruido = rng.laplace(loc=0.0, scale=b)
                valor = C[i, j] + ruido
                valor = float(np.clip(valor, 0.0, 1.0))

                C_ruido[i, j] = valor
                C_ruido[j, i] = 1.0 - valor
            else:
                C_ruido[i, j] = C[i, j]
                C_ruido[j, i] = C[j, i]

    np.fill_diagonal(C_ruido, 0.5)

    return C_ruido


def tecnica_todos(i, j, C):
    """Perturba todos los pares de elementos."""
    return True


def tecnica_aleatoria(rng):
    """
    Perturba cada par con una probabilidad fija.
    La probabilidad se deja como constante interna para que el experimento
    dependa principalmente del parámetro b.
    """
    def criterio(i, j, C):
        return rng.random() < PROBABILIDAD_ALEATORIA

    return criterio


def tecnica_cerca_empate():
    """
    Perturba solo los pares cuyo valor está cerca de 0.5.
    Estos pares representan comparaciones más indecisas o cercanas al empate.
    """
    def criterio(i, j, C):
        return abs(float(C[i, j]) - 0.5) <= UMBRAL_CERCA_EMPATE

    return criterio


def perturbar_matriz(C, b, tecnica, rng):
    """Selecciona la técnica de ruido sobre matriz y la aplica."""
    # if rng is None:
    #     rng = np.random.default_rng()

    if tecnica == "todos":
        criterio = tecnica_todos
    elif tecnica == "aleatoria":
        criterio = tecnica_aleatoria(rng)
    elif tecnica == "cerca_empate":
        criterio = tecnica_cerca_empate()
    else:
        raise ValueError("tecnica debe ser: todos, aleatoria o cerca_empate")

    return perturbar_matriz_laplace(
        C=C,
        b=b,
        criterio=criterio,
        rng=rng,
    )


def aplicar_ruido_matriz(C, b, rng, tecnica="todos"):
    return perturbar_matriz(C, b, tecnica, rng)