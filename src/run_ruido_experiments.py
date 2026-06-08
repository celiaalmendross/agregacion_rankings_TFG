"""
Este módulo ejecuta experimentos de ruido sobre los datasets de PrefLib."""
import argparse

from experimentos.utils_experiments import (
    crear_output_path,
    guardar_csv,
    resolver_dataset,
)

from experimentos.ruido import (
    COLUMNAS_RUIDO,
    ejecutar_dataset_ruido
)


def main():
    parser = argparse.ArgumentParser(
        description="Ejecuta experimentos  centralizados de introducción deruido sobre OBOP."
    )

    parser.add_argument(
        "dataset",
        help="Fichero PrefLib concreto (.soc, .soi, .toc o .toi).",
    )

    parser.add_argument(
        "--metodo",
        required=True,
        choices=["matriz", "rankings", "scores"],
        help="Método de perturbación.",
    )

    parser.add_argument(
        "--tecnica",
        required=True,
        help=(
            "Técnica del método seleccionado. "
            "matriz: todos, aleatoria, cerca_empate; "
            "rankings: aleatoria; "
            "scores: logistic, probit."
        ),
    )

    parser.add_argument(
        "--b",
        required=True,
        help="Valor o valores de b separados por coma.",
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
        carpeta_salida="ruido",
        prefijo="ruido",
    )

    filas = ejecutar_dataset_ruido(dataset_path, args)
    guardar_csv(
        filas=filas,
        output_path=output_path,
        columnas=COLUMNAS_RUIDO,
    )

    print(f"Dataset: {dataset_path.name}")
    print(f"Filas generadas: {len(filas)}")
    print(f"CSV guardado en: {output_path}")


if __name__ == "__main__":
    main()