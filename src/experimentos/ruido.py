"""
Ejecución de experimentos centralizados con ruido.

Cada ejecución trabaja sobre una única instancia PrefLib y una configuración
explícita: método de perturbación, técnica, valores de b y semillas. El objetivo
es comparar el bucket order original con el bucket order obtenido tras introducir
ruido.
"""

import time
import numpy as np

from agregacion_ruido.agregacion_ruido_matriz import perturbar_matriz
from agregacion_ruido.agregacion_ruido_rankings import aplicar_ruido_rankings
from agregacion_ruido.agregacion_ruido_scores_latentes import aplicar_ruido_scores
from experimentos.utils_experiments import (
    cargar_dataset,
    resolver_obop_completo,
    buckets_to_json,
    parse_lista_float,
    parse_lista_int,
)
from obop.obop_ilp import normalizar_obj_value
from metricas.metricas_ruido import distancia_bucket_orders, sensibilidad_ruido, distancia_matrices
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
    "obj_value_norm",
    "obj_value_ruido",
    "obj_value_ruido_norm",
    "n_buckets",
    "n_buckets_ruido",
    "tiempo",
    "kendall_tau",
    "perdida",
    "distancia_entrada",
    "distancia_salida",
    "sensibilidad",
    "buckets_original",
    "buckets_ruido",
]


TECNICAS_MATRIZ = {"todos", "aleatoria", "cerca_empate"}
TECNICAS_RANKINGS = {"aleatoria"}
TECNICAS_SCORES = {"logistic", "probit"}

METODOS_VALIDOS = {"matriz", "rankings", "scores"}


def parse_metodo(texto):
    """
    Valida el método de perturbación indicado por terminal.
    """
    metodo = texto.strip().lower()

    if metodo not in METODOS_VALIDOS:
        raise ValueError(
            f"Método no válido: {metodo}. "
            f"Usa uno de: {sorted(METODOS_VALIDOS)}"
        )

    return metodo

def parse_tecnica(metodo, texto_tecnica):
    """
    Valida la técnica asociada al método de ruido seleccionado.

    En esta versión final no se ejecutan técnicas por defecto: la técnica debe
    indicarse siempre desde terminal para que cada experimento sea explícito.
    """
    tecnica = texto_tecnica.strip().lower()

    if metodo == "matriz":
        tecnicas_validas = TECNICAS_MATRIZ
    elif metodo == "rankings":
        tecnicas_validas = TECNICAS_RANKINGS
    elif metodo == "scores":
        tecnicas_validas = TECNICAS_SCORES
    else:
        raise ValueError(f"Método no reconocido: {metodo}")

    if tecnica not in tecnicas_validas:
        raise ValueError(
            f"Técnica no válida para el método {metodo}: {tecnica}. "
            f"Técnicas disponibles: {sorted(tecnicas_validas)}"
        )

    return tecnica

def obtener_valores_b(args):
    """
    Obtiene los valores de b indicados por la terminal.
    """
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
    C_ruido,
    obj_ruido,
    buckets_ruido,
    tiempo,
):
    """
    Crea una fila del CSV comparando el bucket order original y el perturbado.

    Se registran métricas sobre la entrada, sobre la salida y sobre la pérdida
    de calidad del bucket order perturbado respecto a la matriz original.
    """
    tau = kendall_tau_b(buckets_original, buckets_ruido)
    perdida = perdida_calidad(buckets_original, buckets_ruido, C_original)
    distancia_entrada = distancia_matrices(C_original, C_ruido)
    distancia_salida = distancia_bucket_orders(
        buckets_original,
        buckets_ruido,
        profile.num_alternativas,
    )
    sensibilidad = sensibilidad_ruido(distancia_entrada, distancia_salida)

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
        "obj_value_norm": normalizar_obj_value(obj_original, profile.num_alternativas),
        "obj_value_ruido": obj_ruido,
        "obj_value_ruido_norm": normalizar_obj_value(obj_ruido, profile.num_alternativas),
        "n_buckets": len(buckets_original),
        "n_buckets_ruido": len(buckets_ruido),
        "tiempo": tiempo,
        "kendall_tau": tau,
        "perdida": perdida,
        "distancia_entrada": distancia_entrada,
        "distancia_salida": distancia_salida,
        "sensibilidad": sensibilidad,
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
    """
    Aplica ruido directamente sobre la matriz de precedencias C.
    """
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
        C_ruido=C_ruido,
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
    obj_original,
    buckets_original,
):
    """
    Aplica ruido sobre rankings individuales y reconstruye la matriz C perturbada.
    """
    rng = np.random.default_rng(seed)
    inicio = time.perf_counter()

    C_ruido = aplicar_ruido_rankings(
        rankings=rankings,
        num_alternativas=profile.num_alternativas,
        b=b,
        rng=rng,
    )
    obj_ruido, buckets_ruido = resolver_obop_completo(C_ruido)

    fin = time.perf_counter()

    return crear_fila_ruido(
        dataset_path=dataset_path,
        profile=profile,
        metodo="rankings",
        tecnica="aleatoria",
        b=b,
        seed=seed,
        obj_original=obj_original,
        buckets_original=buckets_original,
        C_original=C,
        C_ruido=C_ruido,
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
    """
    Aplica la estrategia exploratoria basada en scores latentes.
    """
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
        C_ruido=C_ruido,
        obj_ruido=obj_ruido,
        buckets_ruido=buckets_ruido,
        tiempo=fin - inicio,
    )


def ejecutar_configuracion_ruido(
    C,
    rankings,
    profile,
    dataset_path,
    metodo,
    tecnica,
    b,
    seed,
    obj_original,
    buckets_original,
):
    """
    Ejecuta una configuración concreta de ruido.
    """
    if b < 0:
        raise ValueError("El valor de b debe ser no negativo.")

    if metodo == "rankings" and b > 1:
        raise ValueError(
            "En el método rankings, b representa una probabilidad y debe estar en [0, 1]."
        )

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
    Ejecuta las configuraciones de ruido indicadas sobre una instancia PrefLib.
    """
    C, rankings, profile = cargar_dataset(dataset_path)
    obj_original, buckets_original = resolver_obop_completo(C)

    metodo = parse_metodo(args.metodo)
    tecnica = parse_tecnica(metodo, args.tecnica)
    seeds = parse_lista_int(args.seeds)
    valores_b = obtener_valores_b(args)

    filas = []

    for seed in seeds:
        for b in valores_b:
            fila = ejecutar_configuracion_ruido(
                C=C,
                rankings=rankings,
                profile=profile,
                dataset_path=dataset_path,
                metodo=metodo,
                tecnica=tecnica,
                b=b,
                seed=seed,
                obj_original=obj_original,
                buckets_original=buckets_original,
            )
            filas.append(fila)

    return filas
