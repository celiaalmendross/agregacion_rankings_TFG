"""
Ejecución del baseline centralizado sin ruido.

Para una instancia PrefLib, construye la matriz C, resuelve el OBOP exacto y devuelve una fila con el bucket order óptimo y su valor objetivo.
"""

import time

from experimentos.utils_experiments import (
    cargar_dataset,
    resolver_obop_completo,
    buckets_to_json
)
from obop.obop_ilp import normalizar_obj_value

COLUMNAS_BASELINE = [
    "instancia",
    "tipo",
    "n",
    "m",
    "obj_value",
    "obj_value_norm",
    "n_buckets",
    "tiempo",
    "buckets"
]

def ejecutar_baseline_dataset(dataset_path):
    """
    Ejecuta el baseline sobre un dataset.
    """
    C, _, profile = cargar_dataset(dataset_path)

    inicio = time.perf_counter()
    obj_value, buckets = resolver_obop_completo(C)
    fin = time.perf_counter()

    return {
        "instancia": dataset_path.name,
        "tipo": profile.data_type,
        "n": profile.num_alternativas,
        "m": profile.num_voters,
        "obj_value": obj_value,
        "obj_value_norm": normalizar_obj_value(obj_value, profile.num_alternativas),
        "n_buckets": len(buckets),
        "tiempo": fin - inicio,
        "buckets": buckets_to_json(buckets)
    }
