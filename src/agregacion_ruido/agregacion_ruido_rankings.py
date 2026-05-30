from data.preflib_to_C import construir_C_desde_rankings


def eliminar_buckets_vacios(ranking):
    """Elimina los buckets que se hayan quedado sin elementos después de aplicar ruido."""
    return [bucket for bucket in ranking if len(bucket) > 0]


def copiar_ranking(ranking):
    """Crea una copia del ranking para no modificar directamente el ranking original."""
    return [bucket[:] for bucket in ranking]


def obtener_lista_items(ranking):
    """Obtiene todos los ítems del ranking, ignorando la separación en buckets."""
    return [item for bucket in ranking for item in bucket]


def aplicar_intercambio(ranking, num_cambios, rng):
    """
    Aplica la estrategia de intercambio.
    En cada cambio se seleccionan dos ítems al azar y se intercambian sus posiciones.
    Si estaban en buckets distintos, cada ítem pasa al bucket del otro.
    """
    ranking = copiar_ranking(ranking)
    items = obtener_lista_items(ranking)

    if len(items) < 2:
        return ranking

    for _ in range(num_cambios):
        u, v = rng.choice(items, size=2, replace=False)

        pos_u = next(i for i, bucket in enumerate(ranking) if u in bucket)
        pos_v = next(i for i, bucket in enumerate(ranking) if v in bucket)

        ranking[pos_u].remove(u)
        ranking[pos_v].remove(v)

        ranking[pos_u].append(v)
        ranking[pos_v].append(u)

    return eliminar_buckets_vacios(ranking)


def aplicar_movimiento(ranking, num_cambios, rng):
    """
    Aplica la estrategia de movimiento.

    En cada cambio se selecciona un ítem al azar y se desplaza un número
    aleatorio de buckets. El desplazamiento se elige entre 1 y el número total de buckets,
    con dirección aleatoria hacia arriba o hacia abajo.

    Si el ítem pertenece a un bucket con más elementos, se extrae de ese bucket
    y se añade al bucket destino. Si el bucket original queda vacío, se elimina.
    """
     
    ranking = copiar_ranking(ranking)
    if len(ranking) < 2:
        return ranking
    
    for _ in range(num_cambios):
        items = obtener_lista_items(ranking)
        if len(items) == 0 or len(ranking) < 2:
            break

        item = rng.choice(items)
        pos_actual = next(i for i, bucket in enumerate(ranking) if item in bucket)
        movimiento = rng.integers(1, len(ranking))
        direccion = rng.choice([-1, 1])

        nueva_pos = (pos_actual + direccion * movimiento) % len(ranking)    
        ranking[pos_actual].remove(item)
        ranking[nueva_pos].append(item)

        ranking = eliminar_buckets_vacios(ranking)

    return eliminar_buckets_vacios(ranking)


def aplicar_empate(ranking, num_cambios, rng):
    """
    Aplica la estrategia de empate.
    Si el bucket elegido tiene varios ítems, se separa uno de ellos en un nuevo bucket.
    Si el bucket elegido tiene un único ítem, se toma un ítem de otro bucket y se añade al bucket actual, creando o ampliando un empate.
    """
    ranking = copiar_ranking(ranking)

    for _ in range(num_cambios):

        if len(ranking) == 0:
            return ranking
    
        pos = rng.integers(0, len(ranking))
        bucket = ranking[pos]

        if len(bucket) > 1:
            item = rng.choice(bucket)
            bucket.remove(item)

            nueva_pos = rng.integers(0, len(ranking) + 1)
            ranking.insert(nueva_pos, [item])
        else:
            otros_buckets = [
                i for i in range(len(ranking))
                if i != pos and len(ranking[i]) > 0
            ]

            if not otros_buckets:
                continue

            origen = rng.choice(otros_buckets)
            item = rng.choice(ranking[origen])

            ranking[origen].remove(item)
            ranking[pos].append(item)
        ranking = eliminar_buckets_vacios(ranking)

    return eliminar_buckets_vacios(ranking)


def aplicar_local(ranking, num_cambios, rng):
    """
    Aplica la estrategia local.
    En cada cambio se selecciona un tramo consecutivo del ranking y se invierte el orden de sus buckets. Los empates dentro de cada bucket se mantienen.
    """
    ranking = copiar_ranking(ranking)

    if len(ranking) < 2:
        return ranking

    for _ in range(num_cambios):
        i = rng.integers(0, len(ranking) - 1)
        j = rng.integers(i + 2, len(ranking) + 1)
        ranking[i:j] = ranking[i:j][::-1]

    return eliminar_buckets_vacios(ranking)


def calcular_num_cambios(b, n_items):
    """
    Convierte el parámetro b en el número de cambios que se aplican a cada ranking.
    Si b es positivo, se fuerza al menos un cambio para evitar que valores pequeños de b no modifiquen rankings con pocos ítems.
    """
    if b == 0:
        return 0
    return max(1, int(round(b * n_items)))


def aplicar_perturbacion_ranking(ranking, num_cambios, rng):
    """
    Aplica una perturbación aleatoria sobre un ranking individual.

    Para cada ranking se selecciona al azar una de las operaciones básicas:
    intercambio, movimiento, empate o local.
    """
    tecnicas_base = ["intercambio", "movimiento", "empate", "local"]
    tecnica = rng.choice(tecnicas_base)

    if tecnica == "intercambio":
        return aplicar_intercambio(ranking, num_cambios, rng)

    if tecnica == "movimiento":
        return aplicar_movimiento(ranking, num_cambios, rng)

    if tecnica == "empate":
        return aplicar_empate(ranking, num_cambios, rng)

    if tecnica == "local":
        return aplicar_local(ranking, num_cambios, rng)


def aplicar_ruido_rankings(rankings, num_alternativas, b, rng):
    """
    Aplica ruido aleatorio sobre rankings individuales y reconstruye la matriz C.

    Para cada ranking individual se escoge al azar una operación básica entre:
    intercambio, movimiento, empate o local.

    Después, a partir de los rankings modificados, se construye la matriz de
    precedencias que se usará como entrada del OBOP.
    """
    num_cambios = calcular_num_cambios(b, num_alternativas)

    if num_cambios == 0:
        return construir_C_desde_rankings(rankings, num_alternativas)

    rankings_ruido = []

    for ranking in rankings:
        ranking_ruido = aplicar_perturbacion_ranking(
            ranking,
            num_cambios,
            rng
        )
        rankings_ruido.append(ranking_ruido)

    return construir_C_desde_rankings(rankings_ruido, num_alternativas)