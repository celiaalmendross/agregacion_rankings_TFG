"""
Estrategias de agregación de ruido sobre rankings individuales.

Este módulo implementa las estrategias de perturbación aplicadas sobre los rankings individuales.
Hay una única técnica de perturbación, que selecciona aleatoriamente una de las siguientes operaciones elementales:
- Intercambio: se seleccionan dos ítems pertenecientes a buckets distintos y se intercambian sus posiciones.
- Movimiento: se selecciona un ítem al azar y se desplaza un número aleatorio de buckets hacia arriba o hacia abajo.
- Empate: se selecciona un bucket al azar. Si tiene varios ítems, se separa uno de ellos en un nuevo bucket. Si tiene un único ítem, se toma un ítem de otro bucket y se añade al bucket actual, creando o ampliando un empate.
- Local: se selecciona un tramo consecutivo del ranking y se invierte el orden de sus buckets. Los empates dentro de cada bucket se mantienen.

La perturbación se controla mediante dos niveles:

1. El parámetro b indica la probabilidad de seleccionar cada ranking individual
   para ser perturbado.

2. Una vez seleccionado un ranking, se aplica un número de cambios proporcionala su tamaño. Por defecto, se modifica aproximadamente el 10% de  sus alternativas, garantizando al menos un cambio cuando el ranking tiene dos o más alternativas.

"""
import math 

from data.preflib_to_C import construir_C_desde_rankings
PROPORCION_CAMBIOS = 0.10

def eliminar_buckets_vacios(ranking):
    """Elimina los buckets que se hayan quedado sin elementos después de aplicar ruido."""
    return [bucket for bucket in ranking if len(bucket) > 0]


def copiar_ranking(ranking):
    """Crea una copia del ranking para no modificar directamente el ranking original."""
    return [bucket[:] for bucket in ranking]


def obtener_lista_items(ranking):
    """Obtiene todos los ítems del ranking, ignorando la separación en buckets."""
    return [item for bucket in ranking for item in bucket]

def calcular_num_cambios_ranking(ranking, proporcion=PROPORCION_CAMBIOS):
        """Calcula el número de cambios que se aplican a un ranking seleccionado para perturbación."""
        n_items = len(obtener_lista_items(ranking))

        if n_items < 2:
            return 0

        return max(1, math.ceil(proporcion * n_items))


def aplicar_intercambio(ranking, num_cambios, rng):
    """Aplica la estrategia de intercambio efectivo.

    En cada cambio se seleccionan dos buckets distintos y se escoge
    un ítem de cada uno. Después se intercambian ambos ítems.
    De este modo, si existen al menos dos buckets no vacíos, el cambio
    modifica necesariamente alguna relación de precedencia.
    """
    ranking = copiar_ranking(ranking)

    for _ in range(num_cambios):
        ranking = eliminar_buckets_vacios(ranking)

        if len(ranking) < 2:
            break

        pos_u, pos_v = rng.choice(len(ranking), size=2, replace=False)

        u = rng.choice(ranking[pos_u])
        v = rng.choice(ranking[pos_v])

        ranking[pos_u].remove(u)
        ranking[pos_v].remove(v)

        ranking[pos_u].append(v)
        ranking[pos_v].append(u)

        ranking = eliminar_buckets_vacios(ranking)

    return eliminar_buckets_vacios(ranking)


def aplicar_movimiento(ranking, num_cambios, rng):
    """Aplica la estrategia de movimiento.

    En cada cambio se selecciona un ítem al azar y se desplaza un número
    aleatorio de buckets. El desplazamiento se elige entre 1 y el número total de buckets,
    con dirección aleatoria hacia arriba o hacia abajo.
    """
     
    ranking = copiar_ranking(ranking)
    
    for _ in range(num_cambios):
        ranking = eliminar_buckets_vacios(ranking)

        if len(ranking) < 2:
            break
        
        items = obtener_lista_items(ranking)
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
    """Aplica la estrategia de empate.

    Si el bucket elegido tiene varios ítems, se separa uno de ellos en un nuevo bucket.
    Si el bucket elegido tiene un único ítem, se toma un ítem de otro bucket y se añade al bucket actual, creando o ampliando un empate.
    """
    ranking = copiar_ranking(ranking)

    for _ in range(num_cambios):

        ranking = eliminar_buckets_vacios(ranking)
        if len(obtener_lista_items(ranking)) < 2:
            break
    
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
    """Aplica la estrategia local.
    En cada cambio se selecciona un tramo consecutivo del ranking y se invierte el orden de sus buckets.
    """
    ranking = copiar_ranking(ranking)

    if len(ranking) < 2:
        return ranking

    for _ in range(num_cambios):
        ranking = eliminar_buckets_vacios(ranking)

        if len(ranking) < 2:
            break

        i = rng.integers(0, len(ranking) - 1)
        j = rng.integers(i + 2, len(ranking) + 1)
        ranking[i:j] = ranking[i:j][::-1]

    return eliminar_buckets_vacios(ranking)


def aplicar_perturbacion_ranking(ranking, num_cambios, rng):
    """Aplica una perturbación aleatoria sobre un ranking individual.

    Para cada ranking se selecciona al azar una de las operaciones básicas: intercambio, movimiento, empate o local.
    """
 
    ranking = eliminar_buckets_vacios(ranking)

    if num_cambios == 0 or len(obtener_lista_items(ranking)) < 2:
        return copiar_ranking(ranking)
    
    #Si solo hay un bucket, solo la técnica de empate puede producir un cambio real
    if len(ranking) < 2: 
        tecnica = "empate"
    else:
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
        """Aplica ruido aleatorio sobre rankings individuales y reconstruyela matriz C."""
        if b < 0 or b > 1:
            raise ValueError("El parámetro b debe estar en el intervalo [0, 1].")

        rankings_ruido = []

        for ranking in rankings:
            if rng.random() < b:
                num_cambios = calcular_num_cambios_ranking(ranking)
                ranking_ruido = aplicar_perturbacion_ranking(ranking,num_cambios,rng)
            else:
                ranking_ruido = copiar_ranking(ranking)

            rankings_ruido.append(ranking_ruido)

        return construir_C_desde_rankings(rankings_ruido, num_alternativas)