"""Métricas locales para evaluar los resultados federados."""

import numpy as np

from metricas.perdida_calidad import construir_matriz_bucket

def distancia_bucket_C_enmascarada(buckets, C, P):
    """
    Calcula la distancia entre un bucket order y una matriz C, considerando únicamente los pares seleccionados por la máscara P.
    """
    C = np.asarray(C, dtype=float)
    P = np.asarray(P, dtype=float)

    if C.shape != P.shape:
        raise ValueError("C y P deben tener la misma dimensión.")

    B = construir_matriz_bucket(buckets, C.shape[0])
    return float(np.sum(P * np.abs(B - C)))


def normalizar_objetivo_enmascarado(objetivo, P):
    """Normaliza el objetivo usando el número de parees ordanados observados.
    
    En el escenario federado local se divide por la suma de la mascara P"""
    num_pares_observados = float(np.sum(P))

    if num_pares_observados == 0:
        return 0.0

    return float(objetivo / num_pares_observados)


def distancia_matrices_enmascarada(C1, C2, P):
    """
    Calcula la distancia normalizada entre dos matrices usando una máscara local P.
    """
    C1 = np.asarray(C1, dtype=float)
    C2 = np.asarray(C2, dtype=float)
    P = np.asarray(P, dtype=float)

    if C1.shape != C2.shape or C1.shape != P.shape:
        raise ValueError("C1, C2 y P deben tener la misma dimensión.")

    num_pares_observados = float(np.sum(P))

    if num_pares_observados == 0:
        return 0.0

    return float(np.sum(P * np.abs(C1 - C2)) / num_pares_observados)



def calcular_metricas_cliente_federado(
    C_i,
    P_i,
    C_i_ruido,
    buckets_federado,
    obj_local,
):
    obj_federado = distancia_bucket_C_enmascarada(
        buckets_federado,
        C_i,
        P_i,
    )

    
    perdida_local = obj_federado - obj_local

    if abs(perdida_local) < 1e-9:
        perdida_local = 0.0

    return {
        "obj_local": obj_local,
        "obj_federado_en_cliente": obj_federado,
        "perdida_local": perdida_local,
        "obj_local_norm": normalizar_objetivo_enmascarado(obj_local, P_i),
        "obj_federado_en_cliente_norm":
            normalizar_objetivo_enmascarado(obj_federado, P_i),
        "perdida_local_norm":
            normalizar_objetivo_enmascarado(perdida_local, P_i),
        "distancia_entrada_local": distancia_matrices_enmascarada(
            C_i,
            C_i_ruido,
            P_i,
        ),
    }