"""
Implementación del OBOP  mediante ILP.

Este módulo contiene el modelo de Programación Lineal Entera utilizado en el pipeline experimental del TFG. A partir de una matriz de precedencias C, el modelo obtiene un bucket order que minimiza la distancia matricial L1 respecto a dicha matriz.

También incluye una versión ponderada del OBOP, útil para escenarios en los que no todos los pares deben contribuir igual al objetivo. En particular, se utiliza en la simulación federada para resolver problemas locales enmascarados, donde solo se consideran los pares observados por cada cliente.

La salida de este módulo no reconstruye directamente los buckets. Para ello se usa la función reconstruir_bucket_order del módulo bucket_order.py.
"""
import numpy as np
from pyscipopt import Model, quicksum


def _resolver_obop_base(C, pesos = None, mostrar_solver=False):
    """
    Resuelve el OBOP exacto mediante Programación Lineal Entera.
    
    Si pesos es None, se resuelve el OBOP estándar.
    Si pesos no es None, se resuelve el OBOP ponderado:

        min 2 * sum_{r<s} pesos[r,s] * d[r,s]
    donde d[r,s] representa la desviación absoluta entre la relación inducida por el bucket order y la matriz de precedencias C.
    """
    n = C.shape[0]

    if pesos is None:
        pesos = np.ones((n, n), dtype=float)
    else:
        pesos = np.asarray(pesos, dtype=float)

        if pesos.shape != C.shape:
            raise ValueError("pesos debe tener la misma dimensión que C.")

        if np.any(pesos < 0):
            raise ValueError("Los pesos no pueden ser negativos.")

        if not np.allclose(pesos, pesos.T):
            raise ValueError("pesos debe ser una matriz simétrica.")
        

    modelo = Model("OBOP")
    if not mostrar_solver: 
        # Oculta la salida del solver para evitar saturar la consola con mensajes de SCIP.
        modelo.hideOutput()

  
    # x_rs = 1  =>  r va antes o empatado con s
    # x_rs = 0  =>  r va detrás de s

    x = {}
    for r in range(n):
        for s in range(n):
            if r != s:
                x[r, s] = modelo.addVar(vtype="B", name=f"x_{r}_{s}")

    d = {}
    for r in range(n):
        for s in range(r + 1, n):
            d[r, s] = modelo.addVar(vtype="C", lb=0.0, name=f"d_{r}_{s}")


    # Restricción de comparabilidad
    # x_rs + x_sr >= 1

    for r in range(n):
        for s in range(r + 1, n):
            modelo.addCons(x[r, s] + x[s, r] >= 1)
    
    # Restricción de transtividad
    # x_rs + x_st <= 1 + x_rt

    for r in range(n):
        for s in range(n):
            if s == r:
                continue

            for t in range(n):
                if t == r or t == s:
                    continue

                modelo.addCons(x[r, s] + x[s, t] <= 1 + x[r, t])


    # Restricción distancia entre r y s
    #  d_rs >= b_rs - C_rs
    #  d_rs >= C_rs - b_rs
    #  donde b_rs = (x_rs - x_sr + 1) / 2

    for r in range(n):
        for s in range(r + 1, n):
            b_rs = (x[r, s] - x[s, r] + 1) / 2

            modelo.addCons(d[r, s] >= b_rs - float(C[r, s]))
            modelo.addCons(d[r, s] >= float(C[r, s]) - b_rs)


    #  Función objetivo: 
    #     min  2 * sum_{r=1}^{n} sum_{s=r+1}^{n} d_rs

    modelo.setObjective(
        2.0 * quicksum(
            float(pesos[r, s]) * d[r, s]
            for r in range(n)
            for s in range(r + 1, n)
        ),
        sense="minimize",
    )
    
    modelo.optimize()

    estado = modelo.getStatus()
    if estado != "optimal":
        raise RuntimeError(f"SCIP no encontró solución óptima. Estado: {estado}")

    xsol = {}
    for r in range(n):
        for s in range(n):
            if r != s:
                xsol[r, s] = int(round(modelo.getVal(x[r, s])))

    obj = modelo.getObjVal()

    return obj, xsol

def resolver_obop(C, mostrar_solver=False):
    """
    Resuelve el OBOP estándar.

    Devuelve:
        - obj_value: valor objetivo óptimo D(B, C)
        - xsol: diccionario con la solución binaria x[r,s]
    """
    return _resolver_obop_base(
        C=C,
        pesos=None,
        mostrar_solver=mostrar_solver
    )


def resolver_obop_ponderado(C, pesos, mostrar_solver=False):
    """
    Resuelve el OBOP ponderado.

    Esta versión permite asignar un peso a cada par de alternativas. Es útil cuando se desea ignorar algunos pares, por ejemplo usando una máscara P en el OBOP local de la simulación federada.

    Si pesos[r,s] = 0, el par r,s no contribuye a la función objetivo.
    Si pesos[r,s] = 1, el par r,s contribuye normalmente.
    """
    return _resolver_obop_base(
        C=C,
        pesos=pesos,
        mostrar_solver=mostrar_solver
    )


def normalizar_obj_value(obj_value, n):
    """
    Normaliza el valor objetivo del OBOP dividiendo entre n(n-1).
    Esta normalización permite comparar distancias obtenidas en instancias con diferente número de alternativas.
    """
    return float(obj_value / (n * (n - 1)))