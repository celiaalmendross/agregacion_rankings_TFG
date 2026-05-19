from dataclasses import dataclass
from pathlib import Path

import numpy as np

# Formato interno de un ranking con buckets.
OrdenBuckets = tuple[tuple[int, ...], ...] 


@dataclass
class PrefLibProfile:
    file_path: str
    data_type: str
    num_alternativas: int
    num_voters: int | None
    num_unique_orders: int | None
    alternative_names: dict[int, str]
    orders: list[tuple[int, OrdenBuckets]]


def separar_comas(texto):
    """
    Separa una línea por comas, pero respetando los grupos entre llaves.
    Por ejemplo:
    "1,{4,3},2" se separa como ["1", "{4,3}", "2"].
    """
    partes = []
    actual = []
    profundidad = 0

    for caracter in texto:
        if caracter == "{":
            profundidad += 1
            actual.append(caracter)
        elif caracter == "}":
            profundidad -= 1
            actual.append(caracter)
        elif caracter == "," and profundidad == 0:
            token = "".join(actual).strip()
            if token:
                partes.append(token)
            actual = []
        else:
            actual.append(caracter)

    token = "".join(actual).strip()
    if token:
        partes.append(token)

    return partes


def parsear_orden(cadena_orden):
    """
    Convierte un ranking en formato PrefLib en una tupla de buckets.
    Por ejemplo:
    "1,5,6"       -> ((1,), (5,), (6,))
    "1,{4,3},2"   -> ((1,), (4, 3), (2,))
    """
    tokens = separar_comas(cadena_orden.strip())
    buckets = []

    for token in tokens:
        token = token.strip()

        if not token:
            continue

        if token.startswith("{") and token.endswith("}"):
            contenido = token[1:-1].strip()
            if contenido:
                bucket = tuple(
                    int(x.strip()) for x in contenido.split(",") if x.strip()
                )
                buckets.append(bucket)
        else:
            buckets.append((int(token),))

    return tuple(buckets)


def obtener_posiciones_buckets(orden):
    """
    Devuelve un diccionario que indica en qué bucket aparece cada alternativa.
    Si una alternativa no aparece en el ranking, no se incluye en el diccionario.
    Después, al construir C, esos pares simplemente no se comparan.
    """
    posiciones = {}

    for idx_bucket, bucket in enumerate(orden):
        for alternativa in bucket:
            posiciones[int(alternativa)] = idx_bucket

    return posiciones


def normalizar_tipo(path, raw_type=None):
    """
    Obtiene el tipo de dataset PrefLib: soc, soi, toc o toi.
    """
    data_type = (raw_type or path.suffix.lower().lstrip(".")).strip().lower()

    for tipo in ("soc", "soi", "toc", "toi"):
        if data_type == tipo or data_type.endswith(tipo):
            return tipo

    raise ValueError(
        f"Tipo '{data_type}' no soportado. "
        "Solo se admiten ficheros .soc, .soi, .toc y .toi."
    )


def permite_empates(data_type):
    return data_type in {"toc", "toi"}


def es_completo(data_type):
    return data_type in {"soc", "toc"}


def validar_orden(order, data_type, num_alternativas, info_linea=""):
    """
    Comprueba que un ranking sea coherente con el tipo de fichero PrefLib.

    - soc: completo y sin empates.
    - soi: puede ser incompleto, pero sin empates.
    - toc: completo y con posibles empates.
    - toi: puede ser incompleto y puede tener empates.
    """
    items = [alt for bucket in order for alt in bucket]
    items_unicos = set(items)

    if len(items) != len(items_unicos):
        raise ValueError(f"Hay alternativas repetidas {info_linea}: {order}")

    fuera_rango = [
        alt for alt in items
        if alt < 1 or alt > num_alternativas
    ]

    if fuera_rango:
        raise ValueError(
            f"Hay alternativas fuera de 1..{num_alternativas} "
            f"{info_linea}: {fuera_rango}"
        )

    if not permite_empates(data_type):
        buckets_con_empate = [bucket for bucket in order if len(bucket) > 1]
        if buckets_con_empate:
            raise ValueError(
                f"El tipo .{data_type} no permite empates, "
                f"pero aparecen {buckets_con_empate} {info_linea}: {order}"
            )

    if es_completo(data_type):
        esperadas = set(range(1, num_alternativas + 1))
        if items_unicos != esperadas:
            faltan = sorted(esperadas - items_unicos)
            sobran = sorted(items_unicos - esperadas)

            raise ValueError(
                f"El tipo .{data_type} debe contener todas las alternativas "
                f"{info_linea}. Faltan={faltan}, sobran={sobran}"
            )


def cargar_dataset_preflib(path):
    """
    Carga un fichero PrefLib ordinal y devuelve un perfil estructurado.

    Soporta el formato nuevo con cabeceras y el formato antiguo de PrefLib.
    """
    path = Path(path)
    extension = path.suffix.lower().lstrip(".")

    if extension not in {"soc", "soi", "toc", "toi"}:
        raise ValueError(f"Extensión no soportada: {path.suffix}")

    with path.open("r", encoding="utf-8") as fichero:
        lineas = [linea.strip() for linea in fichero if linea.strip()]

    if not lineas:
        raise ValueError(f"El fichero está vacío: {path}")

    if lineas[0].startswith("#"):
        profile = cargar_formato_nuevo(path, lineas)
    else:
        profile = cargar_formato_antiguo(path, lineas)

  
    for i, (_, order) in enumerate(profile.orders, start=1):
        validar_orden(order, profile.data_type, profile.num_alternativas, info_linea=f"en orden #{i}")

    if profile.num_voters is None:
        profile.num_voters = sum(multiplicidad for multiplicidad, _ in profile.orders)

    return profile


def cargar_formato_nuevo(path, lineas):
    """
    Lee el formato PrefLib nuevo, basado en cabeceras con '#'.
    """
    cabeceras = {}
    orders = []

    for linea in lineas:
        if linea.startswith("#"):
            linea = linea[1:].strip()
            if ":" in linea:
                clave, valor = linea.split(":", 1)
                cabeceras[clave.strip().upper()] = valor.strip()
            continue

        if ":" not in linea:
            raise ValueError(f"Línea no válida en formato PrefLib nuevo: {linea}")

        multiplicidad_str, orden_str = linea.split(":", 1)
        multiplicidad = int(multiplicidad_str.strip())
        orden = parsear_orden(orden_str.strip())

        orders.append((multiplicidad, orden))

    data_type = normalizar_tipo(path, cabeceras.get("DATA TYPE"))
    num_alternativas = int(cabeceras["NUMBER ALTERNATIVES"])

    if "NUMBER VOTERS" in cabeceras:
        num_voters = int(cabeceras["NUMBER VOTERS"])
    else:
        num_voters = None

    if "NUMBER UNIQUE ORDERS" in cabeceras:
        num_unique_orders = int(cabeceras["NUMBER UNIQUE ORDERS"])
    else:
        num_unique_orders = len(orders)

    alternative_names = {}

    for clave, valor in cabeceras.items():
        if clave.startswith("ALTERNATIVE NAME "):
            idx = int(clave.replace("ALTERNATIVE NAME ", ""))
            alternative_names[idx] = valor

    return PrefLibProfile(
        file_path=str(path),
        data_type=data_type,
        num_alternativas=num_alternativas,
        num_voters=num_voters,
        num_unique_orders=num_unique_orders,
        alternative_names=alternative_names,
        orders=orders,
    )


def cargar_formato_antiguo(path, lineas):
    """
    Lee el formato PrefLib antiguo.
    """
    num_alternativas = int(lineas[0])
    data_type = normalizar_tipo(path)

    alternative_names = {}
    cursor = 1

    for _ in range(num_alternativas):
        linea = lineas[cursor]
        cursor += 1

        if "," in linea:
            idx_str, nombre = linea.split(",", 1)
            alternative_names[int(idx_str.strip())] = nombre.strip()
        else:
            alternative_names[len(alternative_names) + 1] = linea.strip()

    resumen = [parte.strip() for parte in lineas[cursor].split(",")]
    cursor += 1

    num_voters = int(resumen[0]) if resumen and resumen[0] else None

    if len(resumen) >= 3 and resumen[2]:
        num_unique_orders = int(resumen[2])
    else:
        num_unique_orders = None

    orders = []

    for linea in lineas[cursor:]:
        if "," not in linea:
            raise ValueError(f"Línea no válida en formato PrefLib antiguo: {linea}")

        multiplicidad_str, orden_str = linea.split(",", 1)
        multiplicidad = int(multiplicidad_str.strip())
        orden = parsear_orden(orden_str.strip())

        orders.append((multiplicidad, orden))

    if num_unique_orders is None:
        num_unique_orders = len(orders)

    return PrefLibProfile(
        file_path=str(path),
        data_type=data_type,
        num_alternativas=num_alternativas,
        num_voters=num_voters,
        num_unique_orders=num_unique_orders,
        alternative_names=alternative_names,
        orders=orders,
    )


def extraer_rankings_dataset(profile):
    """
    Extrae los rankings del perfil respetando la multiplicidad.

    Si un ranking aparece con multiplicidad 100, se añade 100 veces a la lista,
    porque representa a 100 votantes con la misma preferencia.
    """
    rankings = []

    for multiplicidad, order in profile.orders:
        ranking = [list(bucket) for bucket in order]

        for _ in range(multiplicidad):
            rankings.append([bucket[:] for bucket in ranking])

    return rankings


def construir_C_desde_rankings(rankings, num_alternativas):
    """
    Construye la matriz de precedencias C a partir de una lista de rankings.
    Cada entrada C[u,v] representa la proporción de veces que la alternativa u
    precede a la alternativa v. Si hay empate, aporta 0.5 a ambas direcciones.
    """
    n = num_alternativas

    victorias = np.zeros((n, n), dtype=float)
    empates = np.zeros((n, n), dtype=float)
    conteos = np.zeros((n, n), dtype=float)

    for order in rankings:
        posiciones = obtener_posiciones_buckets(order)

        for u in range(1, n + 1):
            for v in range(u + 1, n + 1):
                pos_u = posiciones.get(u)
                pos_v = posiciones.get(v)

                if pos_u is None or pos_v is None:
                    continue

                conteos[u - 1, v - 1] += 1
                conteos[v - 1, u - 1] += 1

                if pos_u < pos_v:
                    victorias[u - 1, v - 1] += 1
                elif pos_v < pos_u:
                    victorias[v - 1, u - 1] += 1
                else:
                    empates[u - 1, v - 1] += 1
                    empates[v - 1, u - 1] += 1

    C = np.full((n, n), 0.5, dtype=float)

    for u in range(n):
        for v in range(u + 1, n):
            if conteos[u, v] == 0:
                valor = 0.5
            else:
                valor = (victorias[u, v] + 0.5 * empates[u, v]) / conteos[u, v]

            C[u, v] = valor
            C[v, u] = 1.0 - valor

    np.fill_diagonal(C, 0.5)

    return C


def validar_C(C):
    """
    Comprueba que C sea una matriz de precedencias válida.

    Debe ser cuadrada, tener diagonal 0.5, valores entre 0 y 1,
    y cumplir C[u,v] + C[v,u] = 1. Se usa una pequeña tolerancia
    para evitar problemas de redondeo con números decimales.
    """
    tol = 1e-9
    C = np.asarray(C, dtype=float)

    if C.ndim != 2 or C.shape[0] != C.shape[1]:
        raise ValueError("C debe ser una matriz cuadrada")

    if np.any(C < -tol) or np.any(C > 1 + tol):
        raise ValueError("C tiene valores fuera de [0, 1]")

    if not np.allclose(np.diag(C), 0.5, atol=tol):
        raise ValueError("La diagonal de C debe ser 0.5")

    n = C.shape[0]

    for u in range(n):
        for v in range(u + 1, n):
            if not np.isclose(C[u, v] + C[v, u], 1.0, atol=tol):
                raise ValueError(
                    f"C[{u},{v}] + C[{v},{u}] = {C[u, v] + C[v, u]:.12f}, "
                    "pero debería ser 1"
                )

    return C


def cargar_preflib_a_C(path):
    """
    Carga un dataset PrefLib y devuelve la matriz C, los rankings y el perfil.

    Esta es la función principal que usa el pipeline experimental.
    Primero lee el fichero, después expande los rankings según su multiplicidad
    y finalmente construye la matriz de precedencias.
    """
    profile = cargar_dataset_preflib(path)

    rankings = extraer_rankings_dataset(profile)

    C = construir_C_desde_rankings(rankings, profile.num_alternativas)

    C = validar_C(C)

    return C, rankings, profile