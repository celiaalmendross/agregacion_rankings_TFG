"""
Reconstrucción del bucket order a partir de la solución binaria del OBOP.

El resolvedor ILP devuelve las variables x[r, s], pero la memoria y los experimentos trabajan con bucket orders explícitos, representados como listas de buckets. Este módulo transforma la relación binaria óptima en esa estructura más interpretable.

Ejemplo de salida:
    [[1, 3], [2], [4, 5]]

indica que las alternativas 1 y 3 están empatadas, ambas preceden a 2, y 2 precede a las alternativas 4 y 5.
"""

def reconstruir_bucket_order(xsol, n):
    """
    Reconstruye el bucket order a partir de la solución binaria del OBOP.

    Si x[r,s] = 1 y x[s,r] = 1, los elementos r y s están empatados.
    Si x[r,s] = 1 y x[s,r] = 0, entonces r va antes que s.

    Funcionamiento: 
    1. Se identifican los buckets agrupando las alternativas que están empatadas.
    2. Se ordenan los buckets según la relación de precedencia entre ellos.

    """
    padres = list(range(n))

    def buscar(a):
        # Busca el representante del conjunto de a usando compresión de caminos.
        while padres[a] != a:
            padres[a] = padres[padres[a]]
            a = padres[a]
        return a

    def unir(a, b):
        # Une dos alternativas que pertenecen al mismo bucket.
        raiz_a = buscar(a)
        raiz_b = buscar(b)

        if raiz_a != raiz_b:
            padres[raiz_b] = raiz_a

    for r in range(n):
        for s in range(r + 1, n):
            if xsol[r, s] == 1 and xsol[s, r] == 1:
                unir(r, s)

    grupos = {}
    for alternativa in range(n):
        raiz = buscar(alternativa)
        grupos.setdefault(raiz, []).append(alternativa + 1)

    buckets = list(grupos.values())
    buckets_ref = buckets[:]

    def contar_buckets_anteriores(bucket):
        representante = bucket[0] - 1
        contador = 0

        for otro_bucket in buckets_ref:
            if otro_bucket == bucket:
                continue

            otro_representante = otro_bucket[0] - 1

            if (
                xsol[otro_representante, representante] == 1
                and xsol[representante, otro_representante] == 0
            ):
                contador += 1

        return contador

    # Se ordenan los buckets según cuántos otros buckets los preceden.
    buckets.sort(key=contar_buckets_anteriores)

    return buckets