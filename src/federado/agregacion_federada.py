import numpy as np

from data.preflib_to_C import construir_C_desde_rankings, validar_C
from agregacion_ruido.agregacion_ruido_matriz import perturbar_matriz
from agregacion_ruido.agregacion_ruido_rankings import (
    aplicar_intercambio,
    aplicar_movimiento,
    aplicar_empate,
    aplicar_local,
    calcular_num_cambios,
)

def completar_ranking_con_bucket_final(ranking, num_alternativas):
    """
    Completa un ranking incompleto añadiendo al final un bucket con todas las alternativas que no aparecen.

    Ejemplo:
        ranking = [[1], [3], [6]]
        num_alternativas = 6
    Devuelve:
        [[1], [3], [6], [2, 4, 5]]
    """
    ranking_completo = [list(bucket) for bucket in ranking]

    items_presentes = {
        item
        for bucket in ranking_completo
        for item in bucket
    }

    todas = set(range(1, num_alternativas + 1))
    faltantes = sorted(todas - items_presentes)

    if faltantes:
        ranking_completo.append(faltantes)

    return ranking_completo


def completar_rankings_con_bucket_final(rankings, num_alternativas):
    """
    Aplica completar_ranking_con_bucket_final a una lista de rankings.
    """
    return [
        completar_ranking_con_bucket_final(ranking, num_alternativas)
        for ranking in rankings
    ]


def dividir_rankings_en_clientes(rankings, num_clientes, rng):
    """
    Divide los rankings en num_clientes clientes simulados.
    """
    if num_clientes <= 0:
        raise ValueError("num_clientes debe ser mayor que 0")

    if num_clientes > len(rankings):
        raise ValueError(
            "num_clientes no puede ser mayor que el número de rankings"
        )

    indices = rng.permutation(len(rankings))
    particiones = np.array_split(indices, num_clientes)

    clientes = []

    for particion in particiones:
        cliente = [rankings[int(i)] for i in particion]
        clientes.append(cliente)

    return clientes


def agregar_matrices_clientes(matrices_clientes, pesos_clientes):
    """
    Agrega matrices C locales mediante media ponderada.

    Como los rankings se completan con bucket final, cada C_i
    compara todos los pares de alternativas. Por eso basta con
    ponderar por el número de rankings del cliente.
    """
    if len(matrices_clientes) != len(pesos_clientes):
        raise ValueError("Debe haber un peso por cada matriz local")

    peso_total = sum(pesos_clientes)

    if peso_total <= 0:
        raise ValueError("El peso total debe ser positivo")

    C_global = np.zeros_like(matrices_clientes[0], dtype=float)

    for C_i, peso_i in zip(matrices_clientes, pesos_clientes):
        C_global += peso_i * C_i

    C_global = C_global / peso_total
    np.fill_diagonal(C_global, 0.5)

    return validar_C(C_global)


def perturbar_rankings_cliente(rankings_cliente, num_alternativas, b, tecnica, rng):
    """
    Perturba los rankings de un cliente y devuelve los rankings perturbados.
    A diferencia de aplicar_ruido_rankings, aquí no devuelve C, sino los
    rankings modificados, porque queremos simular que el cliente manda
    rankings perturbados al servidor.
    """
    num_cambios = calcular_num_cambios(b, num_alternativas)

    rankings_ruido = []

    for ranking in rankings_cliente:
        if num_cambios == 0:
            ranking_ruido = [bucket[:] for bucket in ranking]

        elif tecnica == "intercambio":
            ranking_ruido = aplicar_intercambio(ranking, num_cambios, rng)

        elif tecnica == "movimiento":
            ranking_ruido = aplicar_movimiento(ranking, num_cambios, rng)

        elif tecnica == "empate":
            ranking_ruido = aplicar_empate(ranking, num_cambios, rng)

        elif tecnica == "local":
            ranking_ruido = aplicar_local(ranking, num_cambios, rng)

        else:
            raise ValueError(
                "tecnica debe ser: intercambio, movimiento, empate o local"
            )

        ranking_ruido = completar_ranking_con_bucket_final(
            ranking_ruido,
            num_alternativas,
        )

        rankings_ruido.append(ranking_ruido)

    return rankings_ruido


def ejecutar_federado_matrices(
    clientes,
    num_alternativas,
    b,
    tecnica,
    rng,
):
    """
    Escenario A:
    Cada cliente construye su C_i local, la perturba y manda C_i perturbada.
    El servidor agrega las matrices locales perturbadas.
    """
    matrices = []
    pesos = []

    for rankings_cliente in clientes:
        C_local = construir_C_desde_rankings(
            rankings_cliente,
            num_alternativas,
        )

        C_local = validar_C(C_local)

        if b > 0:
            C_local_ruido = perturbar_matriz(
                C=C_local,
                b=b,
                tecnica=tecnica,
                rng=rng,
            )
        else:
            C_local_ruido = C_local

        matrices.append(C_local_ruido)
        pesos.append(len(rankings_cliente))

    return agregar_matrices_clientes(matrices, pesos)


def ejecutar_federado_rankings(
    clientes,
    num_alternativas,
    b,
    tecnica,
    rng,
):
    """
    Escenario B:
    Cada cliente perturba sus rankings y manda esos rankings perturbados.
    El servidor junta rankings perturbados y construye C.
    """
    rankings_perturbados_globales = []

    for rankings_cliente in clientes:
        rankings_cliente_ruido = perturbar_rankings_cliente(
            rankings_cliente=rankings_cliente,
            num_alternativas=num_alternativas,
            b=b,
            tecnica=tecnica,
            rng=rng,
        )

        rankings_perturbados_globales.extend(rankings_cliente_ruido)

    C_global = construir_C_desde_rankings(
        rankings_perturbados_globales,
        num_alternativas,
    )

    return validar_C(C_global)