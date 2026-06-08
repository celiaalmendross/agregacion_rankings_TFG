"""
Este modulo ejecuta el baseline OBOP sin ruido sobre los datasets de PrefLib.
"""

import argparse

from experimentos.utils_experiments import (
    crear_output_path,
    guardar_csv,
    resolver_dataset,
)

from experimentos.baseline import (
    COLUMNAS_BASELINE,
    ejecutar_dataset
)


def main():
    parser = argparse.ArgumentParser(
        description="Ejecuta el baseline centralizado del OBOP sin ruido."
    )

    parser.add_argument(
        "dataset",
        help="Fichero PrefLib concreto (.soc, .soi, .toc, .toi).",
    )

    args = parser.parse_args()

    dataset_path = resolver_dataset(args.dataset)
    output_path = crear_output_path(
        ruta=dataset_path,
        carpeta_salida="baseline",
        prefijo="baseline",
    )

    fila = ejecutar_dataset(dataset_path)
    guardar_csv(
        filas=[fila],
        output_path=output_path,
        columnas=COLUMNAS_BASELINE,
    )

    print(f"Dataset: {dataset_path.name}")
    print("Filas generadas: 1")
    print(f"Salida: {output_path}")


if __name__ == "__main__":
    main()