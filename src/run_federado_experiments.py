"""
Este módulo ejecuta la simulación federada por matrices locales perturbadas sobre los datasets de PrefLib.
"""
import argparse

from experimentos.federado import COLUMNAS_FEDERADO, ejecutar_dataset_federado
from experimentos.utils_experiments import (
    crear_output_path,
    guardar_csv,
    resolver_dataset,
)


def main():
    parser = argparse.ArgumentParser(
        description="Ejecuta la simulación federada por matrices locales perturbadas."
    )

    parser.add_argument(
        "dataset",
        help="Fichero PrefLib concreto (.soc, .soi, .toc o .toi).",
    )

    parser.add_argument(
        "--tecnica",
        required=True,
        choices=["todos", "aleatoria", "cerca_empate"],
        help="Técnica de ruido local sobre matrices.",
    )

    parser.add_argument(
        "--b",
        required=True,
        help="Valor o valores de b separados por coma.",
    )

    parser.add_argument(
        "--num_clientes",
        required=True,
        help="Número o números de clientes separados por coma.",
    )

    parser.add_argument(
        "--seeds",
        default="0,1,2",
        help="Semillas separadas por coma. Por defecto: 0,1,2.",
    )

    args = parser.parse_args()

    dataset_path = resolver_dataset(args.dataset)
    output_path = crear_output_path(
        ruta=dataset_path,
        carpeta_salida="federado",
        prefijo="federado",
    )

    filas = ejecutar_dataset_federado(dataset_path, args)
    guardar_csv(
        filas=filas,
        output_path=output_path,
        columnas=COLUMNAS_FEDERADO,
    )

    print(f"Dataset: {dataset_path.name}")
    print(f"Filas generadas: {len(filas)}")
    print(f"CSV guardado en: {output_path}")


if __name__ == "__main__":
    main()
