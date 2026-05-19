def reconstruir_bucket_order(xsol, n):
    """
    Reconstruye el bucket order a partir de la solución binaria del OBOP.

    Si x[r,s] = 1 y x[s,r] = 1, los elementos r y s están empatados.
    Si x[r,s] = 1 y x[s,r] = 0, entonces r va antes que s.
    """
    padres = list(range(n))

    def buscar(a):
        while padres[a] != a:
            padres[a] = padres[padres[a]]
            a = padres[a]
        return a

    def unir(a, b):
        raiz_a = buscar(a)
        raiz_b = buscar(b)

        if raiz_a != raiz_b:
            padres[raiz_b] = raiz_a

    for r in range(n):
        for s in range(r + 1, n):
            if xsol[r, s] == 1 and xsol[s, r] == 1:
                unir(r, s)

    grupos = {}

    for i in range(n):
        raiz = buscar(i)
        grupos.setdefault(raiz, []).append(i + 1)

    buckets = list(grupos.values())

    def contar_buckets_anteriores(bucket):
        representante = bucket[0] - 1
        contador = 0

        for otro_bucket in buckets:
            if otro_bucket == bucket:
                continue

            otro_representante = otro_bucket[0] - 1

            if (
                xsol[otro_representante, representante] == 1
                and xsol[representante, otro_representante] == 0
            ):
                contador += 1

        return contador

    buckets.sort(key=contar_buckets_anteriores)

    return buckets