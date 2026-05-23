from pathlib import Path
import csv
import json
from datetime import datetime

from data.preflib_to_C import cargar_preflib_a_C
from obop.obop_ilp import resolver_obop as resolver_obop_ilp
from obop.bucket_order import reconstruir_bucket_order


PROJECT_DIR = Path(__file__).resolve().parents[2] 

EXTENSIONES = {".soc", ".soi", ".toc", ".toi"}


def resolver_ruta(ruta):
    ruta = Path(ruta)

    if not ruta.is_absolute():
        ruta = PROJECT_DIR / ruta

    if not ruta.exists():
        raise FileNotFoundError(f"No existe la ruta: {ruta}")

    return ruta


def obtener_datasets(ruta, max_datasets=None):
    """
    Devuelve los datasets que se van a ejecutar.
    Si la ruta es un fichero, devuelve solo ese fichero. 
    Si es una carpeta, busca todos los ficheros PrefLib válidos y permite limitar la cantidad.
    """
    ruta = resolver_ruta(ruta)

    if ruta.is_file():
        if ruta.suffix.lower() not in EXTENSIONES:
            raise ValueError(f"Extensión no válida: {ruta.suffix}")

        return [ruta]

    datasets = []

    for extension in EXTENSIONES:
        datasets.extend(ruta.rglob(f"*{extension}"))

    datasets = sorted(datasets)

    if max_datasets is not None:
        datasets = datasets[:max_datasets]

    return datasets


def cargar_dataset(dataset_path):
    """
    Carga un dataset PrefLib y devuelve la matriz C, los rankings y el perfil.
    """
    return cargar_preflib_a_C(dataset_path)


def resolver_obop_completo(C):
    """
    Resuelve el OBOP mediante ILP y reconstruye el bucket order final.
    Devuelve el valor objetivo y el consenso en forma de buckets.
    """
    n = C.shape[0]

    obj_value, xsol = resolver_obop_ilp(C)
    buckets = reconstruir_bucket_order(xsol, n)

    return float(obj_value), buckets


def crear_output_path(ruta, carpeta_salida, prefijo):
    """
    Crea la ruta del CSV de salida usando el nombre del dataset y la fecha actual.
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
    return [float(x.strip()) for x in texto.split(",") if x.strip()]


def parse_lista_int(texto):
    return [int(x.strip()) for x in texto.split(",") if x.strip()]
