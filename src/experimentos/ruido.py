import time
import numpy as np

from experimentos.utils_experiments import (
    cargar_dataset,
    resolver_obop_completo,
    buckets_to_json,
    parse_lista_float,
    parse_lista_int,
)

from agregacion_ruido.agregacion_ruido_matriz import perturbar_matriz
from agregacion_ruido.agregacion_ruido_rankings import aplicar_ruido_rankings
from agregacion_ruido.agregacion_ruido_scores_latentes import aplicar_ruido_scores

from metricas.kendall_tau import kendall_tau_b
from metricas.perdida_calidad import perdida_calidad


COLUMNAS_RUIDO = [
    "instancia",
    "tipo",
    "n",
    "m",
    "metodo",
    "tecnica",
    "parametros",
    "seed",
    "obj_value",
    "obj_value_ruido",
    "n_buckets",
    "n_buckets_ruido",
    "tiempo",
    "kendall_tau",
    "perdida",
    "buckets_original",
    "buckets_ruido",
]


TECNICAS_MATRIZ = {"todos", "aleatoria", "cerca_empate"}
TECNICAS_RANKINGS = {"intercambio", "movimiento", "empate", "local"}
TECNICAS_SCORES = {"logistic", "probit"}

METODOS_VALIDOS = {"matriz", "rankings", "scores", "todos"}
TODAS_TECNICAS = TECNICAS_MATRIZ | TECNICAS_RANKINGS | TECNICAS_SCORES


def parse_metodo(texto):
    metodo = texto.strip().lower()

    if metodo not in METODOS_VALIDOS:
        raise ValueError(
            f"Método no válido: {metodo}. "
            f"Usa uno de: {sorted(METODOS_VALIDOS)}"
        )

    return metodo


def tecnicas_por_metodo(metodo):
    if metodo == "matriz":
        return sorted(TECNICAS_MATRIZ)

    if metodo == "rankings":
        return sorted(TECNICAS_RANKINGS)

    if metodo == "scores":
        return sorted(TECNICAS_SCORES)

    if metodo == "todos":
        return sorted(TODAS_TECNICAS)

    raise ValueError(f"Método no reconocido: {metodo}")


def metodo_de_tecnica(tecnica):
    if tecnica in TECNICAS_MATRIZ:
        return "matriz"

    if tecnica in TECNICAS_RANKINGS:
        return "rankings"

    if tecnica in TECNICAS_SCORES:
        return "scores"

    raise ValueError(f"Técnica no reconocida: {tecnica}")


def parse_tecnicas(texto_tecnica, metodo):
    """
    Devuelve las técnicas que se van a ejecutar.

    Si no se indica una técnica concreta, se ejecutan todas las técnicas
    del método seleccionado.
    """
    tecnicas_permitidas = set(tecnicas_por_metodo(metodo))

    if texto_tecnica is None:
        return sorted(tecnicas_permitidas)

    tecnicas = [
        tecnica.strip()
        for tecnica in texto_tecnica.split(",")
        if tecnica.strip()
    ]

    tecnicas_invalidas = [
        tecnica for tecnica in tecnicas
        if tecnica not in TODAS_TECNICAS
    ]

    if tecnicas_invalidas:
        raise ValueError(
            f"Técnicas no válidas: {tecnicas_invalidas}. "
            f"Técnicas disponibles: {sorted(TODAS_TECNICAS)}"
        )

    tecnicas_fuera_metodo = [
        tecnica for tecnica in tecnicas
        if tecnica not in tecnicas_permitidas
    ]

    if tecnicas_fuera_metodo:
        raise ValueError(
            f"Estas técnicas no pertenecen al método '{metodo}': "
            f"{tecnicas_fuera_metodo}"
        )

    return sorted(set(tecnicas))


def valores_b(args):
    return parse_lista_float(args.b)


def crear_fila_ruido(
    dataset_path,
    profile,
    metodo,
    tecnica,
    b,
    seed,
    obj_original,
    buckets_original,
    C_original,
    obj_ruido,
    buckets_ruido,
    tiempo,
):
    """
    Crea una fila del CSV comparando el consenso original
    con el consenso obtenido tras introducir ruido.
    """
    tau = kendall_tau_b(buckets_original, buckets_ruido)
    perdida = perdida_calidad(buckets_original, buckets_ruido, C_original)

    return {
        "instancia": dataset_path.name,
        "tipo": profile.data_type,
        "n": profile.num_alternativas,
        "m": profile.num_voters,
        "metodo": metodo,
        "tecnica": tecnica,
        "parametros": f"b={b}",
        "seed": seed,
        "obj_value": obj_original,
        "obj_value_ruido": obj_ruido,
        "n_buckets": len(buckets_original),
        "n_buckets_ruido": len(buckets_ruido),
        "tiempo": tiempo,
        "kendall_tau": tau,
        "perdida": perdida,
        "buckets_original": buckets_to_json(buckets_original),
        "buckets_ruido": buckets_to_json(buckets_ruido),
    }


def ejecutar_ruido_matriz(
    C,
    dataset_path,
    profile,
    seed,
    b,
    tecnica,
    obj_original,
    buckets_original,
):
    rng = np.random.default_rng(seed)
    inicio = time.perf_counter()

    C_ruido = perturbar_matriz(C, b, tecnica, rng)
    obj_ruido, buckets_ruido = resolver_obop_completo(C_ruido)

    fin = time.perf_counter()

    return crear_fila_ruido(
        dataset_path=dataset_path,
        profile=profile,
        metodo="matriz",
        tecnica=tecnica,
        b=b,
        seed=seed,
        obj_original=obj_original,
        buckets_original=buckets_original,
        C_original=C,
        obj_ruido=obj_ruido,
        buckets_ruido=buckets_ruido,
        tiempo=fin - inicio,
    )


def ejecutar_ruido_rankings(
    C,
    rankings,
    dataset_path,
    profile,
    seed,
    b,
    tecnica,
    obj_original,
    buckets_original,
):
    rng = np.random.default_rng(seed)
    inicio = time.perf_counter()

    C_ruido = aplicar_ruido_rankings(
        rankings=rankings,
        num_alternativas=profile.num_alternativas,
        b=b,
        rng=rng,
        tecnica=tecnica,
    )

    obj_ruido, buckets_ruido = resolver_obop_completo(C_ruido)

    fin = time.perf_counter()

    return crear_fila_ruido(
        dataset_path=dataset_path,
        profile=profile,
        metodo="rankings",
        tecnica=tecnica,
        b=b,
        seed=seed,
        obj_original=obj_original,
        buckets_original=buckets_original,
        C_original=C,
        obj_ruido=obj_ruido,
        buckets_ruido=buckets_ruido,
        tiempo=fin - inicio,
    )


def ejecutar_ruido_scores(
    C,
    dataset_path,
    profile,
    seed,
    b,
    tecnica,
    obj_original,
    buckets_original,
):
    rng = np.random.default_rng(seed)
    inicio = time.perf_counter()

    C_ruido = aplicar_ruido_scores(C, b, rng, tecnica)
    obj_ruido, buckets_ruido = resolver_obop_completo(C_ruido)

    fin = time.perf_counter()

    return crear_fila_ruido(
        dataset_path=dataset_path,
        profile=profile,
        metodo="scores",
        tecnica=tecnica,
        b=b,
        seed=seed,
        obj_original=obj_original,
        buckets_original=buckets_original,
        C_original=C,
        obj_ruido=obj_ruido,
        buckets_ruido=buckets_ruido,
        tiempo=fin - inicio,
    )


def ejecutar_configuracion_ruido(
    C,
    rankings,
    profile,
    dataset_path,
    tecnica,
    b,
    seed,
    obj_original,
    buckets_original,
):
    if b < 0:
        raise ValueError("El valor de b debe ser no negativo.")

    metodo = metodo_de_tecnica(tecnica)

    if metodo == "matriz":
        return ejecutar_ruido_matriz(
            C=C,
            dataset_path=dataset_path,
            profile=profile,
            seed=seed,
            b=b,
            tecnica=tecnica,
            obj_original=obj_original,
            buckets_original=buckets_original,
        )

    if metodo == "rankings":
        return ejecutar_ruido_rankings(
            C=C,
            rankings=rankings,
            dataset_path=dataset_path,
            profile=profile,
            seed=seed,
            b=b,
            tecnica=tecnica,
            obj_original=obj_original,
            buckets_original=buckets_original,
        )

    if metodo == "scores":
        return ejecutar_ruido_scores(
            C=C,
            dataset_path=dataset_path,
            profile=profile,
            seed=seed,
            b=b,
            tecnica=tecnica,
            obj_original=obj_original,
            buckets_original=buckets_original,
        )

    raise ValueError(f"Método no reconocido: {metodo}")


def ejecutar_dataset_ruido(dataset_path, args):
    """
    Ejecuta todas las configuraciones de ruido sobre un dataset.
    """
    C, rankings, profile = cargar_dataset(dataset_path)

    obj_original, buckets_original = resolver_obop_completo(C)

    metodo = parse_metodo(args.metodo)
    tecnicas = parse_tecnicas(args.tecnica, metodo)
    seeds = parse_lista_int(args.seeds)

    filas = []

    for seed in seeds:
        for tecnica in tecnicas:
            for b in valores_b(args):
                fila = ejecutar_configuracion_ruido(
                    C=C,
                    rankings=rankings,
                    profile=profile,
                    dataset_path=dataset_path,
                    tecnica=tecnica,
                    b=b,
                    seed=seed,
                    obj_original=obj_original,
                    buckets_original=buckets_original,
                )

                filas.append(fila)

    return filas