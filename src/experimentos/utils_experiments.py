"""
Utilidades comunes para los experimentos del TFG.

Este módulo reúne funciones auxiliares usadas por los scripts experimentales:
resolución de rutas, carga de una instancia PrefLib, resolución completa del
OBOP, guardado de resultados en CSV y conversión de bucket orders a texto.
"""

from pathlib import Path
import csv
import json
from datetime import datetime

from data.preflib_to_C import cargar_preflib_a_C
from obop.obop_ilp import resolver_obop as resolver_obop_ilp
from obop.bucket_order import reconstruir_bucket_order
from obop.obop_ilp import resolver_obop_ponderado

#Directorio raíz del proyecto. Se asume que este script está en src/experimentos/utils_experiments.py
PROJECT_DIR = Path(__file__).resolve().parents[2] 

EXTENSIONES = {".soc", ".soi", ".toc", ".toi"}


def resolver_ruta(ruta):
    """
    Resuelve una ruta relativa al proyecto o una ruta absoluta.
    """
    ruta = Path(ruta)

    if not ruta.is_absolute():
        ruta = PROJECT_DIR / ruta

    if not ruta.exists():
        raise FileNotFoundError(f"No existe la ruta: {ruta}")

    return ruta

def resolver_dataset(ruta):
    """
    Valida que la ruta indicada corresponde a un único fichero PrefLib.

    En la versión final de los experimentos no se ejecutan carpetas completas:
    cada comando trabaja sobre una instancia concreta. Esto simplifica la
    reproducción de los resultados y evita lógica adicional no utilizada en
    la memoria.
    """
    ruta = resolver_ruta(ruta)

    if not ruta.is_file():
        raise ValueError(
            "La ruta debe ser un fichero PrefLib concreto, no una carpeta."
        )

    if ruta.suffix.lower() not in EXTENSIONES:
        raise ValueError(
            f"Extensión no válida: {ruta.suffix}. "
            f"Extensiones admitidas: {sorted(EXTENSIONES)}"
        )

    return ruta


def cargar_dataset(dataset_path):
    """
    Carga un dataset PrefLib y devuelve la matriz C, los rankings y el perfil.
    """
    return cargar_preflib_a_C(dataset_path)


def resolver_obop_completo(C):
    """
    Resuelve el OBOP mediante ILP y reconstruye el bucket order final.
    Devuelve el valor objetivo y el bucket order en forma de buckets.
    """
    n = C.shape[0]

    obj_value, xsol = resolver_obop_ilp(C)
    buckets = reconstruir_bucket_order(xsol, n)

    return float(obj_value), buckets


def resolver_obop_ponderado_completo(C, pesos):
    """
    Resuelve el OBOP ponderado mediante ILP y reconstruye el bucket order final."""
    n = C.shape[0]

    obj_value, xsol = resolver_obop_ponderado(
        C,
        pesos=pesos,
    )

    buckets = reconstruir_bucket_order(xsol, n)

    return float(obj_value), buckets


def crear_output_path(ruta, carpeta_salida, prefijo):
    """
    Construye la ruta del CSV de salida dentro de outputs/.

    El nombre incluye el prefijo del experimento, el nombre de la ruta ejecutada
    y una marca temporal para evitar sobrescribir resultados anteriores.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta = Path(ruta)

    return PROJECT_DIR / "outputs" / carpeta_salida / f"{prefijo}_{ruta.name}_{timestamp}.csv"


def guardar_csv(filas, output_path, columnas):
    """
    Guarda una lista de filas en un fichero CSV.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as fichero:
        writer = csv.DictWriter(fichero, fieldnames=columnas)
        writer.writeheader()
        writer.writerows(filas)


def buckets_to_json(buckets):
    """
    Convierte el bucket order a texto para guardarlo en el CSV.
    """
    return json.dumps(buckets, ensure_ascii=False)


def parse_lista_float(texto):
    """
    Convierte una cadena separada por comas en una lista de valores float.

    Ejemplo: "0.1,0.5,0.3" -> [0.1, 0.5, 0.3]
    """
    return [float(x.strip()) for x in texto.split(",") if x.strip()]


def parse_lista_int(texto):
    """
    Convierte una cadena separada por comas en una lista de valores int.

    Ejemplo: "1,5,3" -> [1, 5, 3]
    """
    return [int(x.strip()) for x in texto.split(",") if x.strip()]
