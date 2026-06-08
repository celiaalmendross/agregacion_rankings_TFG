"""
Funciones auxiliares para la simulación federada por matrices locales.

El protocolo implementado es una simulación federada controlada:

1. Los rankings se dividen entre K clientes.
2. Cada cliente construye localmente dos matrices:
   - W_i(a,b): evidencia acumulada de que a precede a b.
   - M_i(a,b): número de rankings locales que comparan el par (a,b).
3. Cada cliente obtiene su matriz local C_i a partir de W_i y M_i.
4. Se introduce ruido local sobre C_i únicamente en pares observados.
5. El servidor agrega las matrices perturbadas usando M_i como peso por par.

La agregación global se realiza par a par:

    C_fed(a,b) = sum_i M_i(a,b) * C_i_ruido(a,b) / sum_i M_i(a,b)

Si ningún cliente aporta información sobre un par, se asigna el valor neutro 0.5.
"""

import numpy as np

from data.preflib_to_C import obtener_posiciones_buckets, validar_C
from agregacion_ruido.agregacion_ruido_matriz import (
    PROBABILIDAD_ALEATORIA,
    UMBRAL_CERCA_EMPATE,
)


def dividir_rankings_en_clientes(rankings, num_clientes, rng):
    """
    Divide los rankings en clientes simulados.

    La división se hace aleatorizando los índices con la semilla indicada
    y repartiendo los rankings en particiones de tamaño lo más parecido posible.
    """
    if num_clientes <= 0:
        raise ValueError("num_clientes debe ser mayor que 0.")

    if num_clientes > len(rankings):
        raise ValueError(
            "num_clientes no puede ser mayor que el número de rankings."
        )

    indices = rng.permutation(len(rankings))
    particiones = np.array_split(indices, num_clientes)

    return [
        [rankings[int(indice)] for indice in particion]
        for particion in particiones
    ]


def construir_W_M_desde_rankings(rankings, num_alternativas):
    """
    Construye las matrices W y M a partir de los rankings de un cliente.

    W[a,b] acumula la evidencia de que la alternativa a precede a b:
    - 1.0 si a precede a b;
    - 0.5 si a y b están empatadas;
    - 0.0 si b precede a a.

    M[a,b] cuenta cuántos rankings contienen simultáneamente a y b.
    En rankings incompletos, si alguna alternativa del par no aparece,
    ese ranking no aporta información sobre dicho par.
    """
    W = np.zeros((num_alternativas, num_alternativas), dtype=float)
    M = np.zeros((num_alternativas, num_alternativas), dtype=float)

    for ranking in rankings:
        posiciones = obtener_posiciones_buckets(ranking)
        alternativas_observadas = sorted(posiciones)

        for idx_u in range(len(alternativas_observadas)):
            for idx_v in range(idx_u + 1, len(alternativas_observadas)):
                u = alternativas_observadas[idx_u]
                v = alternativas_observadas[idx_v]

                i = u - 1
                j = v - 1

                M[i, j] += 1.0
                M[j, i] += 1.0

                if posiciones[u] < posiciones[v]:
                    W[i, j] += 1.0
                elif posiciones[v] < posiciones[u]:
                    W[j, i] += 1.0
                else:
                    W[i, j] += 0.5
                    W[j, i] += 0.5

    np.fill_diagonal(W, 0.0)
    np.fill_diagonal(M, 0.0)

    return W, M


def construir_C_desde_W_M(W, M):
    """
    Construye una matriz de precedencias C a partir de W y M.

    Si M[a,b] > 0, se calcula C[a,b] = W[a,b] / M[a,b].
    Si M[a,b] = 0, se asigna C[a,b] = 0.5 como valor neutro por ausencia
    de información sobre ese par.
    """
    if W.shape != M.shape:
        raise ValueError("W y M deben tener la misma dimensión.")

    n = W.shape[0]
    C = np.full((n, n), 0.5, dtype=float)

    for i in range(n):
        for j in range(i + 1, n):
            if M[i, j] > 0:
                valor = float(W[i, j] / M[i, j])
                valor = float(np.clip(valor, 0.0, 1.0))
            else:
                valor = 0.5

            C[i, j] = valor
            C[j, i] = 1.0 - valor

    np.fill_diagonal(C, 0.5)

    return validar_C(C)


def construir_clientes_locales(clientes, num_alternativas):
    """
    Construye la información local de cada cliente.

    Para cada cliente se calcula:

        rankings_i -> W_i, M_i -> C_i

    No se completan rankings incompletos. Los pares no observados quedan
    reflejados en M_i(a,b)=0.
    """
    clientes_locales = []

    for cliente_id, rankings_cliente in enumerate(clientes, start=1):
        W_i, M_i = construir_W_M_desde_rankings(
            rankings=rankings_cliente,
            num_alternativas=num_alternativas,
        )

        C_i = construir_C_desde_W_M(W_i, M_i)

        clientes_locales.append(
            {
                "cliente_id": cliente_id,
                "m_cliente": len(rankings_cliente),
                "W_i": W_i,
                "M_i": M_i,
                "C_i": C_i,
            }
        )

    return clientes_locales


def criterio_perturbacion_federado(C, i, j, tecnica, rng):
    """
    Decide si se perturba el par (i,j) según la técnica indicada.
    """
    if tecnica == "todos":
        return True

    if tecnica == "aleatoria":
        return rng.random() < PROBABILIDAD_ALEATORIA

    if tecnica == "cerca_empate":
        return abs(float(C[i, j]) - 0.5) <= UMBRAL_CERCA_EMPATE

    raise ValueError("tecnica debe ser: todos, aleatoria o cerca_empate.")


def perturbar_matriz_observada(C, M, b, tecnica, rng):
    """
    Perturba una matriz local C_i solo en pares observados.

    Si M[i,j] = 0, el cliente no tiene información real sobre ese par.
    En ese caso no se añade ruido y se mantiene el valor neutro 0.5.
    """
    if b < 0:
        raise ValueError("El parámetro b debe ser no negativo.")

    C = validar_C(C)
    n = C.shape[0]
    C_ruido = C.copy()

    for i in range(n):
        for j in range(i + 1, n):
            if M[i, j] <= 0:
                C_ruido[i, j] = 0.5
                C_ruido[j, i] = 0.5
                continue

            if b > 0 and criterio_perturbacion_federado(C, i, j, tecnica, rng):
                ruido = rng.laplace(loc=0.0, scale=b)
                valor = float(np.clip(C[i, j] + ruido, 0.0, 1.0))

                C_ruido[i, j] = valor
                C_ruido[j, i] = 1.0 - valor
            else:
                C_ruido[i, j] = C[i, j]
                C_ruido[j, i] = C[j, i]

    np.fill_diagonal(C_ruido, 0.5)

    return validar_C(C_ruido)


def agregar_matrices_clientes(matrices_clientes, matrices_M):
    """
    Agrega las matrices locales perturbadas usando M_i como peso por par.

    La agregación no usa una media global por cliente, sino una media
    específica para cada par de alternativas. Así, un cliente solo aporta
    peso sobre los pares que realmente aparecen en sus rankings locales.
    """
    if len(matrices_clientes) != len(matrices_M):
        raise ValueError("Debe haber una matriz M por cada matriz C.")

    if not matrices_clientes:
        raise ValueError("Debe haber al menos una matriz local.")

    n = matrices_clientes[0].shape[0]
    W_global = np.zeros((n, n), dtype=float)
    M_global = np.zeros((n, n), dtype=float)

    for C_i_ruido, M_i in zip(matrices_clientes, matrices_M):
        W_global += C_i_ruido * M_i
        M_global += M_i

    return construir_C_desde_W_M(W_global, M_global)


def perturbar_y_agregar_clientes(clientes_locales, b, tecnica, rng):
    """
    Simula el protocolo federado con ruido local.

    Para cada cliente se obtiene C_i_ruido aplicando ruido sobre los pares
    observados de C_i. Después, el servidor agrega las matrices locales
    perturbadas usando las matrices M_i como denominadores por par.
    """
    matrices_ruido = []
    matrices_M = []
    clientes_resultado = []

    for cliente in clientes_locales:
        C_i_ruido = perturbar_matriz_observada(
            C=cliente["C_i"],
            M=cliente["M_i"],
            b=b,
            tecnica=tecnica,
            rng=rng,
        )

        matrices_ruido.append(C_i_ruido)
        matrices_M.append(cliente["M_i"])

        cliente_resultado = dict(cliente)
        cliente_resultado["C_i_ruido"] = C_i_ruido

        clientes_resultado.append(cliente_resultado)

    C_federada = agregar_matrices_clientes(
        matrices_clientes=matrices_ruido,
        matrices_M=matrices_M,
    )

    return C_federada, clientes_resultado
