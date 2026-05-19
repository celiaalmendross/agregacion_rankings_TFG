from pyscipopt import Model, quicksum


def resolver_obop(C, mostrar_solver=False):
    """
    Resuelve el OBOP exacto mediante programación lineal entera.

    A partir de la matriz de precedencias C, obtiene la relación óptima entre los ítems permitiendo empates. 
    Devuelve el valor objetivo y las variables binarias de la solución.
    """
    n = C.shape[0]

    modelo = Model("OBOP")

    if not mostrar_solver:
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


    # Restricción comparabilidad
    # x_rs + x_sr >= 1

    for r in range(n):
        for s in range(r + 1, n):
            modelo.addCons(x[r, s] + x[s, r] >= 1)
    
    # Restricción transtividad
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
        2.0 * quicksum(d[r, s] for r in range(n) for s in range(r + 1, n)),
        sense="minimize"
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