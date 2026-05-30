import time

import numpy as np

from experimentos.utils_experiments import (
    cargar_dataset,
    resolver_obop_completo,
    buckets_to_json,
    parse_lista_float,
    parse_lista_int
)

from data.preflib_to_C import construir_C_desde_rankings, validar_C

from metricas.kendall_tau import kendall_tau_b
from metricas.perdida_calidad import perdida_calidad, distancia_bucket_C

from federado.agregacion_federada import (
    completar_rankings_con_bucket_final,
    dividir_rankings_en_clientes,
    ejecutar_federado_matrices,
    ejecutar_federado_rankings,
)


COLUMNAS_FEDERADO = [
    "instancia",
    "tipo",
    "n",
    "m",
    "num_clientes",
    "modo_federado",
    "tecnica",
    "parametros",
    "seed",
    "obj_value_central",
    "obj_value_federado",
    "perdida",
    "n_buckets_central",
    "n_buckets_federado",
    "kendall_tau",
    "buckets_central",
    "buckets_federado",
    "tiempo"
]


TECNICAS_FED_MATRICES = {"todos", "aleatoria", "cerca_empate"}

MODOS_FEDERADOS_VALIDOS = {"matrices", "rankings", "todos"}

def parse_modo_federado(texto):
    modo = texto.strip().lower()

    if modo not in MODOS_FEDERADOS_VALIDOS:
        raise ValueError(
            f"Modo federado no válido: {modo}. "
            f"Usa uno de: {sorted(MODOS_FEDERADOS_VALIDOS)}"
        )

    return modo

def configuraciones_federadas(modo, texto_tecnica=None):
    """
    Devuelve pares (modo_federado, tecnica).

    En modo rankings no existe técnica como parámetro. Se usa 'aleatoria'
    solo como etiqueta en el CSV.
    """
    if modo == "rankings":
        if texto_tecnica is not None:
            raise ValueError(
                "El modo federado rankings no admite --tecnica. "
                "Usa solo: --modo rankings --b ..."
            )

        return [("rankings", "aleatoria")]

    if modo == "matrices":
        tecnicas_disponibles = TECNICAS_FED_MATRICES

    elif modo == "todos":
        if texto_tecnica is not None:
            raise ValueError(
                "Con --modo todos no indiques --tecnica."
            )

        return (
            [("matrices", tecnica) for tecnica in sorted(TECNICAS_FED_MATRICES)]
            + [("rankings", "aleatoria")]
        )

    else:
        raise ValueError(f"Modo federado no reconocido: {modo}")

    if texto_tecnica is None:
        return [
            (modo, tecnica)
            for tecnica in sorted(tecnicas_disponibles)
        ]

    tecnicas = [
        tecnica.strip()
        for tecnica in texto_tecnica.split(",")
        if tecnica.strip()
    ]

    invalidas = [
        tecnica for tecnica in tecnicas
        if tecnica not in tecnicas_disponibles
    ]

    if invalidas:
        raise ValueError(
            f"Técnicas no válidas para el modo {modo}: {invalidas}. "
            f"Técnicas disponibles: {sorted(tecnicas_disponibles)}"
        )

    return [
        (modo, tecnica)
        for tecnica in sorted(set(tecnicas))
    ]


def crear_fila_federado(
    dataset_path,
    profile,
    num_clientes,
    modo_federado,
    tecnica,
    b,
    seed,
    C_central,
    obj_central,
    buckets_central,
    obj_federado,
    buckets_federado,
    tiempo,
):
    """
    Crea una fila del CSV comparando el consenso centralizado
    con el consenso federado.
    """
    tau = kendall_tau_b(buckets_central, buckets_federado)

    perdida = perdida_calidad(
        buckets_central,
        buckets_federado,
        C_central,
    )

    return {
        "instancia": dataset_path.name,
        "tipo": profile.data_type,
        "n": profile.num_alternativas,
        "m": profile.num_voters,
        "num_clientes": num_clientes,
        "modo_federado": modo_federado,
        "tecnica": tecnica,
        "parametros": f"b={b}",
        "seed": seed,
        "obj_value_central": obj_central,
        "obj_value_federado": obj_federado,
        "perdida": perdida,
        "n_buckets_central": len(buckets_central),
        "n_buckets_federado": len(buckets_federado),
        "kendall_tau": tau,
        "buckets_central": buckets_to_json(buckets_central),
        "buckets_federado": buckets_to_json(buckets_federado),
        "tiempo": tiempo
    }


def ejecutar_configuracion_federada(
    rankings_completos,
    C_central,
    profile,
    dataset_path,
    num_clientes,
    modo_federado,
    tecnica,
    b,
    seed,
    obj_central,
    buckets_central,
):
    """
    Ejecuta una configuración concreta del experimento federado.

    Puede ser:
    - modo_federado = "matrices":
        cada cliente calcula C_i, la perturba y manda C_i perturbada.
    - modo_federado = "rankings":
        cada cliente perturba sus rankings y manda rankings perturbados.
    """
    if b < 0:
        raise ValueError("El valor de b debe ser no negativo.")

    rng = np.random.default_rng(seed)

    clientes = dividir_rankings_en_clientes(
        rankings=rankings_completos,
        num_clientes=num_clientes,
        rng=rng,
    )

    inicio = time.perf_counter()

    if modo_federado == "matrices":
        C_federada = ejecutar_federado_matrices(
            clientes=clientes,
            num_alternativas=profile.num_alternativas,
            b=b,
            tecnica=tecnica,
            rng=rng,
        )

    elif modo_federado == "rankings":
        C_federada = ejecutar_federado_rankings(
            clientes=clientes,
            num_alternativas=profile.num_alternativas,
            b=b,
            rng=rng,
        )

    else:
        raise ValueError(f"Modo federado no reconocido: {modo_federado}")

    C_federada = validar_C(C_federada)

    obj_federado, buckets_federado = resolver_obop_completo(C_federada)

    fin = time.perf_counter()

    return crear_fila_federado(
        dataset_path=dataset_path,
        profile=profile,
        num_clientes=num_clientes,
        modo_federado=modo_federado,
        tecnica=tecnica,
        b=b,
        seed=seed,
        C_central=C_central,
        obj_central=obj_central,
        buckets_central=buckets_central,
        obj_federado=obj_federado,
        buckets_federado=buckets_federado,
        tiempo=fin - inicio,
    )


def ejecutar_dataset_federado(dataset_path, args):
    """
    Ejecuta todas las configuraciones federadas sobre un dataset.
    """
    _, rankings, profile = cargar_dataset(dataset_path)

    rankings_completos = completar_rankings_con_bucket_final(
        rankings=rankings,
        num_alternativas=profile.num_alternativas,
    )

    C_central = construir_C_desde_rankings(
        rankings_completos,
        profile.num_alternativas,
    )

    C_central = validar_C(C_central)

    obj_central, buckets_central = resolver_obop_completo(C_central)

    modo = parse_modo_federado(args.modo)
    configuraciones = configuraciones_federadas(modo, args.tecnica)
    seeds = parse_lista_int(args.seeds)
    valores_b = parse_lista_float(args.b)
    clientes_lista = parse_lista_int(args.clientes)

    filas = []

    for num_clientes in clientes_lista:
        for seed in seeds:
            for modo_federado, tecnica in configuraciones:

                for b in valores_b:
                    fila = ejecutar_configuracion_federada(
                        rankings_completos=rankings_completos,
                        C_central=C_central,
                        profile=profile,
                        dataset_path=dataset_path,
                        num_clientes=num_clientes,
                        modo_federado=modo_federado,
                        tecnica=tecnica,
                        b=b,
                        seed=seed,
                        obj_central=obj_central,
                        buckets_central=buckets_central,
                    )

                    filas.append(fila)

    return filas
