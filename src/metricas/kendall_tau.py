from math import isnan
from scipy.stats import kendalltau


def bucket_order_a_posiciones(bucket_order):
    """
    Convierte un bucket order en un diccionario ítem -> posición.

    Los ítems que están en el mismo bucket reciben la misma posición, lo que permite representar empates.
    """
    posiciones = {}

    for indice_bucket, bucket in enumerate(bucket_order):
        for item in bucket:
            if item in posiciones:
                raise ValueError(f"El ítem {item} aparece repetido")
            
            posiciones[item] = indice_bucket

    return posiciones


def kendall_tau_b(bucket_order_1, bucket_order_2):
    """
    Calcula la similitud Kendall tau-b entre dos bucket orders.

    Primero transforma cada bucket order en un vector de posiciones. 
    Si dos ítems están empatados, tendrán el mismo valor en el vector. 
    Después se usa la implementación de scipy, que permite tratar empates.
    """
    posiciones_1 = bucket_order_a_posiciones(bucket_order_1)
    posiciones_2 = bucket_order_a_posiciones(bucket_order_2)

    if set(posiciones_1.keys()) != set(posiciones_2.keys()):
        raise ValueError("Ambos bucket orders deben contener los mismos ítems")

    items = sorted(posiciones_1.keys())

    vector_1 = [posiciones_1[item] for item in items]
    vector_2 = [posiciones_2[item] for item in items]

    tau, _ = kendalltau(vector_1, vector_2, variant="b")

    if isnan(tau):
        return 1.0 if vector_1 == vector_2 else 0.0

    return float(tau)