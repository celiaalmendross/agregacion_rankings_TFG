"""
Métricas para evaluar la calidad de los resultados en el entorno federado.
Este módulo implementa las métricas globales y locales para evaluar la calidad de los resultados obtenidos en la simulación federada.
"""

from metricas.kendall_tau import kendall_tau_b
from metricas.perdida_calidad import distancia_bucket_C
from metricas.metricas_ruido import (
    distancia_matrices,
    distancia_bucket_orders,
    sensibilidad_ruido,
)
from obop.obop_ilp import normalizar_obj_value


def calcular_metricas_globales_federadas(
    C_central,
    C_federada,
    buckets_central,
    buckets_federado,
):
    """
    Calcula las métricas globales de la simulación federada.

    Se compara la matriz centralizada original con la matriz federada
    agregada, y el bucket order centralizado con el bucket order federado.
    """
    n = C_central.shape[0]

    distancia_entrada_global = distancia_matrices(
        C_central,
        C_federada,
    )

    distancia_salida_global = distancia_bucket_orders(
        buckets_central,
        buckets_federado,
        n,
    )

    sensibilidad_global = sensibilidad_ruido(
        distancia_entrada_global,
        distancia_salida_global,
    )

    kendall_tau_global = kendall_tau_b(
        buckets_central,
        buckets_federado,
    )

    return {
        "kendall_tau_global": kendall_tau_global,
        "distancia_entrada_global": distancia_entrada_global,
        "distancia_salida_global": distancia_salida_global,
        "sensibilidad_global": sensibilidad_global,
    }


def calcular_metricas_cliente_federado(
    C_i,
    C_i_ruido,
    buckets_federado,
    obj_local,
):
    """
    Calcula las métricas locales de un cliente en el entorno federado.

    La pérdida local mide cuánto empeora el bucket order federado
    al evaluarlo sobre la matriz local original del cliente.

    La distancia_entrada_local mide cuánto ruido se ha introducido
    en la matriz local del cliente: d(C_i, C_i_ruido).
    """
    n = C_i.shape[0]

    obj_federado_en_cliente = distancia_bucket_C(
        buckets_federado,
        C_i,
    )

    perdida_local = obj_federado_en_cliente - obj_local
    if abs(perdida_local) < 1e-9:
        perdida_local = 0.0 
    
    distancia_entrada_local = distancia_matrices(
        C_i,
        C_i_ruido,
    )

    return {
        "obj_local": obj_local,
        "obj_local_norm": normalizar_obj_value(obj_local, n),

        "obj_federado_en_cliente": obj_federado_en_cliente,
        "obj_federado_en_cliente_norm": normalizar_obj_value(
            obj_federado_en_cliente,
            n,
        ),

        "perdida_local": perdida_local,
        "perdida_local_norm": normalizar_obj_value(
            perdida_local,
            n,
        ),

        "distancia_entrada_local": distancia_entrada_local,
    }