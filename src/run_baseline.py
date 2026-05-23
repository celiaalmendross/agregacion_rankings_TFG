import argparse

from experimentos.utils_experiments import (
    obtener_datasets,
    crear_output_path,
    guardar_csv
)

from experimentos.baseline import (
    COLUMNAS_BASELINE,
    ejecutar_dataset
)



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

            guardar_csv(filas=resultados, output_path=output_path, columnas=COLUMNAS_BASELINE)            
            print(f"{dataset_path.name}: OK")

        except Exception as error:
            print(f"{dataset_path.name}: ERROR - {error}")

    guardar_csv(filas=resultados, output_path=output_path, columnas=COLUMNAS_BASELINE)

    print(f"\nFilas generadas: {len(resultados)}")
    print(f"CSV guardado en: {output_path}")


if __name__ == "__main__":
    main()