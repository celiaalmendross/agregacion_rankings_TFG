"""
Ejecución de la simulación federada por matrices locales.

Cada ejecución trabaja sobre una única instancia PrefLib. Los rankings se dividen
entre varios clientes, cada cliente construye su matriz local, se introduce ruido
local sobre dichas matrices y el servidor agrega las matrices perturbadas.
"""

import time

import numpy as np

from experimentos.utils_experiments import (
    cargar_dataset,
    resolver_obop_completo,
    resolver_obop_ponderado_completo,
    buckets_to_json,
    parse_lista_float,
    parse_lista_int,
)

from data.preflib_to_C import validar_C

from metricas.kendall_tau import kendall_tau_b
from metricas.metricas_ruido import (
    distancia_matrices,
    distancia_bucket_orders,
    sensibilidad_ruido,
)
from federado.agregacion_federada import dividir_rankings_en_clientes
from federado.cliente import ClienteFederado
from federado.servidor import ServidorFederado

COLUMNAS_FEDERADO = [
    "instancia",
    "tipo",
    "n",
    "m",
    "num_clientes",
    "cliente_id",
    "m_cliente",
    "metodo_federado",
    "tecnica",
    "b",
    "seed",
    "kendall_tau_global",
    "obj_local",
    "obj_federado_en_cliente",
    "perdida_local",
    "obj_local_norm",
    "obj_federado_en_cliente_norm",
    "perdida_local_norm",
    "distancia_entrada_local",
    "distancia_entrada_global",
    "distancia_salida_global",
    "sensibilidad_global",
    "n_buckets_local",
    "n_buckets_federado",
    "buckets_local",
    "buckets_federado",
    "tiempo",
]


TECNICAS_FED_MATRICES = {"todos", "aleatoria", "cerca_empate"}


def parse_tecnica_federada(texto_tecnica):
    """
    Valida la técnica de ruido local sobre matrices.
    """
    tecnica = texto_tecnica.strip().lower()

    if tecnica not in TECNICAS_FED_MATRICES:
        raise ValueError(
            f"Técnica federada no válida: {tecnica}. "
            f"Técnicas disponibles: {sorted(TECNICAS_FED_MATRICES)}"
        )

    return tecnica

def obtener_lista_num_clientes(texto_num_clientes, m_real):
    """
    Valida los valores de K indicados por terminal.
    """
    lista = parse_lista_int(texto_num_clientes)
    lista_validada = []

    for k in lista:
        if k <= 0:
            raise ValueError("El número de clientes debe ser mayor que 0.")

        if k > m_real:
            raise ValueError(
                f"num_clientes={k} no puede ser mayor que el número de rankings ({m_real})."
            )

        lista_validada.append(k)

    return lista_validada

def crear_filas_clientes(
    dataset_path,
    profile,
    m_real,
    num_clientes,
    metodo_federado,
    tecnica,
    b,
    seed,
    metricas_globales,
    buckets_federado,
    clientes_simulados,
    metricas_clientes,
    tiempo,
):
    """
    Crea una fila por cliente para una configuración federada.
    """
    filas = []

    for cliente, metricas_cliente in zip(clientes_simulados, metricas_clientes):

        fila = {
            "instancia": dataset_path.name,
            "tipo": profile.data_type,
            "n": profile.num_alternativas,
            "m": m_real,
            "num_clientes": num_clientes,
            "cliente_id": cliente.cliente_id,
            "m_cliente": cliente.m_cliente,
            "metodo_federado": metodo_federado,
            "tecnica": tecnica,
            "b": b,
            "seed": seed,
            "kendall_tau_global": metricas_globales["kendall_tau_global"],
            "distancia_entrada_global": metricas_globales["distancia_entrada_global"],
            "distancia_salida_global": metricas_globales["distancia_salida_global"],
            "sensibilidad_global": metricas_globales["sensibilidad_global"],
            **metricas_cliente,
            "n_buckets_local": len(cliente.buckets_local),
            "n_buckets_federado": len(buckets_federado),
            "buckets_local": buckets_to_json(cliente.buckets_local),
            "buckets_federado": buckets_to_json(buckets_federado),
            "tiempo": tiempo,
        }

        filas.append(fila)

    return filas

def calcular_metricas_globales_federadas(
    C_central,
    C_federada,
    buckets_central,
    buckets_federado,
):
    n = C_central.shape[0]

    distancia_entrada_global = distancia_matrices(
        C_central,
        C_federada,
    )

    distancia_salida_global = distancia_bucket_orders(
        buckets_central,
        buckets_federado,
        n,
    )

    sensibilidad_global = sensibilidad_ruido(
        distancia_entrada_global,
        distancia_salida_global,
    )

    kendall_tau_global = kendall_tau_b(
        buckets_central,
        buckets_federado,
    )

    return {
        "kendall_tau_global": kendall_tau_global,
        "distancia_entrada_global": distancia_entrada_global,
        "distancia_salida_global": distancia_salida_global,
        "sensibilidad_global": sensibilidad_global,
    }

def ejecutar_dataset_federado(dataset_path, args):
    """
    Ejecuta la simulación federada para una instancia PrefLib.
    """
    C_central, rankings, profile = cargar_dataset(dataset_path)

    m_real = len(rankings)
    C_central = validar_C(C_central)

    _, buckets_central = resolver_obop_completo(C_central)

    seeds = parse_lista_int(args.seeds)
    valores_b = parse_lista_float(args.b)
    tecnica = parse_tecnica_federada(args.tecnica)
    lista_num_clientes = obtener_lista_num_clientes(args.num_clientes, m_real)

    filas = []

    for num_clientes in lista_num_clientes:
        for seed in seeds:
            rng_division = np.random.default_rng(seed)

            particiones_clientes = dividir_rankings_en_clientes(
                rankings=rankings,
                num_clientes=num_clientes,
                rng=rng_division,
            )
            clientes = []

            for cliente_id, rankings_cliente in enumerate(particiones_clientes, start=1):
                cliente = ClienteFederado(
                    cliente_id=cliente_id,
                    rankings=rankings_cliente,
                    num_alternativas=profile.num_alternativas,
                )
                cliente.construir_informacion_local()
                cliente.resolver_bucket_order_local(resolver_obop_ponderado_completo)
                clientes.append(cliente)

            for b in valores_b:
                rng_ruido = np.random.default_rng(seed)

                inicio = time.perf_counter()

                for cliente in clientes:
                    cliente.perturbar_matriz_local(b=b, tecnica=tecnica, rng=rng_ruido)

                mensajes_clientes = [cliente.crear_mensaje_para_servidor() for cliente in clientes]

                servidor = ServidorFederado()
                servidor.recibir_mensajes_clientes(mensajes_clientes)
                C_federada = servidor.agregar_matrices()
                _, buckets_federado = servidor.resolver_bucket_order_federado(resolver_obop_completo)

                buckets_para_clientes = servidor.obtener_bucket_order_para_clientes()

                metricas_local = [cliente.evaluar_bucket_order_federado(buckets_para_clientes) for cliente in clientes]

                metricas_globales = calcular_metricas_globales_federadas(
                    C_central=C_central,
                    C_federada=C_federada,
                    buckets_central=buckets_central,
                    buckets_federado=buckets_federado,
                )

                fin = time.perf_counter()

                filas.extend(
                    crear_filas_clientes(
                        dataset_path=dataset_path,
                        profile=profile,
                        m_real=m_real,
                        num_clientes=num_clientes,
                        metodo_federado="matrices",
                        tecnica=tecnica,
                        b=b,
                        seed=seed,
                        metricas_globales=metricas_globales,
                        buckets_federado=buckets_federado,
                        clientes_simulados=clientes,
                        metricas_clientes=metricas_local,
                        tiempo=fin - inicio,
                    )
                )

    return filas
