import argparse

from experimentos.utils_experiments import (
    obtener_datasets,
    crear_output_path,
    guardar_csv,
)

from experimentos.federado import (
    COLUMNAS_FEDERADO,
    ejecutar_dataset_federado,
)


def main():
    parser = argparse.ArgumentParser(
        description="Ejecuta experimentos federados sobre OBOP."
    )

    parser.add_argument("ruta", help="Carpeta o fichero PrefLib.")

    parser.add_argument(
        "max_datasets",
        type=int,
        nargs="?",
        default=None,
        help="Número máximo de datasets si se pasa una carpeta.",
    )

    parser.add_argument(
        "--modo",
        default="todos",
        help="Modo federado: matrices, rankings o todos.",
    )

    parser.add_argument(
        "--tecnica",
        default=None,
        help="Técnicas concretas separadas por coma.",
    )

    parser.add_argument(
        "--clientes",
        default="3",
        help="Número de clientes simulados. Puede ser: 2,3,5.",
    )

    parser.add_argument(
        "--seeds",
        default="0,1,2",
        help="Semillas separadas por coma.",
    )

    parser.add_argument(
        "--b",
        default="0,0.01,0.05,0.10",
        help="Valores de b separados por coma.",
    )

    args = parser.parse_args()

    datasets = obtener_datasets(
        ruta=args.ruta,
        max_datasets=args.max_datasets,
    )

    output_path = crear_output_path(
        ruta=args.ruta,
        carpeta_salida="federado",
        prefijo="federado",
    )

    print(f"Datasets seleccionados: {len(datasets)}")
    print(f"Salida: {output_path}")

    todas_filas = []

    for dataset_path in datasets:
        try:
            filas = ejecutar_dataset_federado(dataset_path, args)
            todas_filas.extend(filas)

            guardar_csv(
                filas=todas_filas,
                output_path=output_path,
                columnas=COLUMNAS_FEDERADO,
            )

            print(f"{dataset_path.name}: {len(filas)} filas")

        except Exception as error:
            print(f"{dataset_path.name}: ERROR - {error}")

    guardar_csv(
        filas=todas_filas,
        output_path=output_path,
        columnas=COLUMNAS_FEDERADO,
    )

    print(f"\nFilas generadas: {len(todas_filas)}")
    print(f"CSV guardado en: {output_path}")


if __name__ == "__main__":
    main()