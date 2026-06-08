"""
Este módulo contiene el código para ejecutar el baseline sobre un dataset. El baseline consiste en resolver el OBOP mediante programación lineal entera, y sin añadir ruido."""

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

def ejecutar_dataset(dataset_path):
    """
    Ejecuta el baseline sobre un dataset.
    """
    C, _ , profile = cargar_dataset(dataset_path)

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
