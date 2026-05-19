import argparse
import time

from utils_experiments import (
    obtener_datasets,
    cargar_dataset,
    resolver_obop_completo,
    crear_output_path,
    guardar_csv,
    buckets_to_json,
)


COLUMNAS = [
    "instancia",
    "tipo",
    "n",
    "m",
    "obj_value",
    "n_buckets",
    "tiempo",
    "buckets",
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
        "n_buckets": len(buckets),
        "tiempo": fin - inicio,
        "buckets": buckets_to_json(buckets),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Ejecuta el baseline OBOP sin ruido."
    )

    parser.add_argument(
        "ruta",
        help="Carpeta o fichero PrefLib.",
    )

    parser.add_argument(
        "max_datasets",
        type=int,
        nargs="?",
        default=None,
        help="Número máximo de datasets si se pasa una carpeta.",
    )

    args = parser.parse_args()

    datasets = obtener_datasets(ruta=args.ruta, max_datasets=args.max_datasets)

    output_path = crear_output_path(ruta=args.ruta, carpeta_salida="baseline", prefijo="baseline")

    print(f"Datasets seleccionados: {len(datasets)}")
    print(f"Salida: {output_path}")

    resultados = []

    for dataset_path in datasets:
        try:
            fila = ejecutar_dataset(dataset_path)
            resultados.append(fila)

            guardar_csv(filas=resultados, output_path=output_path, columnas=COLUMNAS)            
            print(f"{dataset_path.name}: OK")

        except Exception as error:
            print(f"{dataset_path.name}: ERROR - {error}")

    guardar_csv(filas=resultados, output_path=output_path, columnas=COLUMNAS)

    print(f"\nFilas generadas: {len(resultados)}")
    print(f"CSV guardado en: {output_path}")


if __name__ == "__main__":
    main()