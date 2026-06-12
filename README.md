# Privacidad en agregación de rankings: Aplicación del Aprendizaje Federado

Este repositorio contiene el código desarrollado para el Trabajo Fin de Grado de **Celia Almendros Saelices**.

## Objetivo del proyecto

El proyecto se centra en la agregación de rankings con empates mediante el **Optimal Bucket Order Problem (OBOP)**. El objetivo del OBOP es obtener un **bucket order**, es decir, una ordenación completa de las alternativas en la que se permiten empates.

El código implementa un pipeline experimental que permite:

- cargar datasets de rankings en formato PrefLib
- construir la matriz de precedencias por pares \(C\)
- resolver el OBOP mediante Programación Lineal Entera
- aplicar distintas estrategias de ruido
- implementar una simulación federada basada en matrices locales
- comparar el bucket order original con los bucket orders obtenidos tras introducir ruido o ejecutar una simulación federada.

El objetivo principal de los experimentos es analizar cómo cambia el bucket order obtenido por el OBOP cuando se perturba la información de entrada, tanto en un escenario centralizado como en una simulación federada.

---

## Estructura del repositorio

La estructura general del repositorio es la siguiente:

```text
agregacion_rankings_TFG/
│
├── data/
│   ├── 00006_skate/
│   ├── 00035_breakfast/
│   ├── 00068_poland_local_elections/
│   ├── 00071_voter-autrement-in-situ/
│   └── README.md
│
├── outputs/
│   ├── baseline/
│   ├── ruido/
│   ├── federado/
│   └── README.md   
│
├── src/
│   ├── agregacion_ruido/
│   │   ├── agregacion_ruido_matriz.py
│   │   ├── agregacion_ruido_rankings.py
│   │   └── agregacion_ruido_scores_latentes.py
│   │
│   ├── data/
│   │   └── preflib_to_C.py
│   │
│   ├── experimentos/
│   │   ├── baseline.py
│   │   ├── ruido.py
│   │   ├── federado.py
│   │   └── utils_experiments.py
│   │
│   ├── federado/
│   │   ├── cliente.py
│   │   ├── servidor.py
│   │   └── agregacion_federada.py
│   │
│   ├── metricas/
│   │   ├── kendall_tau.py
│   │   ├── perdida_calidad.py
│   │   ├── metricas_ruido.py
│   │   └── metricas_federada.py
│   │
│   ├── obop/
│   │   ├── obop_ilp.py
│   │   └── bucket_order.py
│   │
│   ├── run_baseline.py
│   ├── run_ruido_experiments.py
│   └── run_federado_experiments.py
│
├── requirements.txt
├── .gitignore
└── README.md
```

La carpeta `src/` contiene el código fuente del proyecto.

La carpeta `data/` contiene los datasets utilizados.

La carpeta `outputs/` contiene los resultados generados por las ejecuciones.

---

## Instalación

Se recomienda utilizar un entorno virtual de Python para evitar conflictos con otras instalaciones o proyectos.

El archivo `requirements.txt` contiene las librerías necesarias para ejecutar el proyecto.

---

## Ejecución

Los scripts deben ejecutarse desde la raíz del proyecto, es decir, desde la carpeta donde se encuentran `README.md`, `src/`, `data/` y `outputs/`.

En esta versión del proyecto, cada ejecución se realiza sobre un fichero PrefLib concreto. Para ejecutar varios datasets, se lanza el script varias veces cambiando la ruta del fichero.

---

## 1. Baseline centralizado

El baseline consiste en construir la matriz de precedencias original \(C\), resolver el OBOP exacto mediante programación lineal entera y obtener el bucket order de referencia.

La ejecución general es:

```bash
python src/run_baseline.py <fichero_prefLib>
```

Ejemplo:

```bash
python src/run_baseline.py data/00035_breakfast/00035-00000006.soc
```

Los resultados se guardan en:

```text
outputs/baseline/
```

Los ficheros generados incluyen información como:

- nombre de la instancia;
- tipo de dataset;
- número de alternativas;
- número de rankings;
- valor objetivo del OBOP;
- valor objetivo normalizado;
- número de buckets;
- tiempo de ejecución;
- bucket order obtenido.

---

## 2. Experimentos con ruido

Los experimentos con ruido perturban los datos de entrada, resuelven de nuevo el OBOP y comparan el bucket order perturbado con el bucket order original.

La ejecución general es:

```bash
python src/run_ruido_experiments.py <fichero_prefLib> --metodo <metodo> --tecnica <tecnica> --b <valores_b> [--seeds <semillas>]
```

Parámetros:

| Parámetro | Descripción |
|---|---|
| `--metodo` | Familia de ruido: `matriz`, `rankings` o `scores` |
| `--tecnica` | Técnica concreta dentro del método elegido |
| `--b` | Valor o valores del parámetro de ruido separados por coma |
| `--seeds` | Semillas aleatorias separadas por coma. Por defecto: `0,1,2` |

Los resultados se guardan en:

```text
outputs/ruido/
```

---

### 2.1. Ruido sobre matriz

Este método introduce ruido directamente sobre la matriz de precedencias \(C\).

Técnicas disponibles:

| Técnica | Descripción |
|---|---|
| `todos` | Perturba todos los pares de la matriz |
| `aleatoria` | Perturba una parte aleatoria de los pares |
| `cerca_empate` | Perturba solo pares cercanos al empate |

Ejemplo:

```bash
python src/run_ruido_experiments.py data/00035_breakfast/00035-00000006.soc --metodo matriz --tecnica cerca_empate --b 0.01,0.05,0.10
```

---

### 2.2. Ruido sobre rankings

Este método introduce ruido sobre los rankings individuales antes de reconstruir la matriz de precedencias perturbada.

En esta versión del proyecto se utiliza una única técnica experimental para rankings:

| Técnica | Descripción |
|---|---|
| `aleatoria` | Selecciona rankings con probabilidad \(b\) y aplica una perturbación elemental aleatoria |

Ejemplo:

```bash
python src/run_ruido_experiments.py data/00035_breakfast/00035-00000006.soc --metodo rankings --tecnica aleatoria --b 0.10,0.20,0.30
```

---

### 2.3. Ruido sobre scores latentes

Este método estima scores a partir de la matriz \(C\), introduce ruido sobre dichos scores y reconstruye una matriz de precedencias.

Técnicas disponibles:

| Técnica | Descripción |
|---|---|
| `logistic` | Reconstrucción mediante función logística |
| `probit` | Reconstrucción mediante función probit |

Ejemplo:

```bash
python src/run_ruido_experiments.py data/00068_poland_local_elections/00068-00000301.soi --metodo scores --tecnica logistic --b 0,0.01,0.05,0.10
```

---

## 3. Simulación federada

La simulación federada divide los rankings de una instancia entre varios clientes. Cada cliente construye su información local, introduce ruido sobre su matriz local y el servidor agrega la información recibida para resolver el OBOP global.

La ejecución general es:

```bash
python src/run_federado_experiments.py <fichero_prefLib> --tecnica <tecnica> --b <valores_b> --num_clientes <valores_K> [--seeds <semillas>]
```

Parámetros:

| Parámetro | Descripción |
|---|---|
| `--tecnica` | Técnica de ruido local sobre matrices: `todos`, `aleatoria` o `cerca_empate` |
| `--b` | Valor o valores del parámetro de ruido separados por coma |
| `--num_clientes` | Número o números de clientes separados por coma |
| `--seeds` | Semillas aleatorias separadas por coma. Por defecto: `0,1,2` |

Ejemplo:

```bash
python src/run_federado_experiments.py data/00068_poland_local_elections/00068-00000301.soi --tecnica cerca_empate --b 0,0.01,0.05,0.10 --num_clientes 3,5,10
```

Los resultados se guardan en:

```text
outputs/federado/
```

---

## Métricas registradas

Los experimentos guardan distintas métricas para analizar el efecto del ruido y de la simulación federada.

### Métricas de los experimentos con ruido

Los ficheros de `outputs/ruido/` incluyen, entre otras, las siguientes columnas:

- `instancia`: nombre del fichero PrefLib;
- `tipo`: tipo de dataset (`soc`, `soi`, `toc` o `toi`);
- `n`: número de alternativas;
- `m`: número de rankings;
- `metodo`: familia de ruido utilizada;
- `tecnica`: técnica concreta aplicada;
- `parametros`: valor del parámetro \(b\);
- `seed`: semilla aleatoria;
- `obj_value`: valor objetivo original;
- `obj_value_norm`: valor objetivo original normalizado;
- `obj_value_ruido`: valor objetivo obtenido sobre la matriz perturbada;
- `obj_value_ruido_norm`: valor objetivo perturbado normalizado;
- `n_buckets`: número de buckets del bucket order original;
- `n_buckets_ruido`: número de buckets del bucket order perturbado;
- `tiempo`: tiempo de ejecución;
- `kendall_tau`: coeficiente de correlación entre el bucket order original y el perturbado;
- `perdida`: pérdida de calidad respecto a la matriz original;
- `distancia_entrada`: distancia entre la matriz original y la matriz perturbada;
- `distancia_salida`: distancia entre el bucket order original y el perturbado;
- `sensibilidad`: relación entre el cambio en la salida y el cambio en la entrada;
- `buckets_original`: bucket order original;
- `buckets_ruido`: bucket order perturbado.

### Métricas de los experimentos federados

Los ficheros de `outputs/federado/` incluyen, entre otras, las siguientes columnas:

- `instancia`: nombre del fichero PrefLib;
- `tipo`: tipo de dataset;
- `n`: número de alternativas;
- `m`: número de rankings;
- `num_clientes`: número de clientes de la simulación;
- `cliente_id`: identificador del cliente;
- `m_cliente`: número de rankings asignados al cliente;
- `metodo_federado`: método federado utilizado;
- `tecnica`: técnica de ruido local;
- `b`: valor del parámetro de ruido;
- `seed`: semilla aleatoria;
- `kendall_tau_global`: coeficiente de correlación entre el bucket order centralizado y el bucket order federado;
- `obj_local`: valor objetivo del bucket order local del cliente;
- `obj_federado_en_cliente`: valor objetivo del bucket order federado evaluado sobre la matriz local del cliente;
- `perdida_local`: pérdida de calidad local;
- `obj_local_norm`: valor objetivo local normalizado;
- `obj_federado_en_cliente_norm`: valor objetivo federado evaluado localmente, normalizado;
- `perdida_local_norm`: pérdida local normalizada;
- `distancia_entrada_local`: distancia entre la matriz local original y la matriz local perturbada;
- `distancia_entrada_global`: distancia entre la matriz centralizada y la matriz federada;
- `distancia_salida_global`: distancia entre el bucket order centralizado y el bucket order federado;
- `sensibilidad_global`: relación entre el cambio de salida y el cambio de entrada;
- `n_buckets_local`: número de buckets del bucket order local;
- `n_buckets_federado`: número de buckets del bucket order federado;
- `buckets_local`: bucket order local;
- `buckets_federado`: bucket order federado;
- `tiempo`: tiempo de ejecución.

---

## Carpetas de resultados

La carpeta `outputs/` almacena los resultados generados por las ejecuciones del proyecto.

```text
outputs/
├── baseline/
├── ruido/
└── federado/
```

Los resultados se guardan en formato CSV para facilitar su análisis posterior y su inclusión en la memoria del TFG.

---

## Notas sobre reproducibilidad

Para garantizar la reproducibilidad de los experimentos, los scripts permiten fijar semillas aleatorias mediante el parámetro `--seeds`.

Por defecto, los experimentos con ruido y federados utilizan:

```text
0,1,2
```

como conjunto de semillas.

Ejemplo:

```bash
python src/run_ruido_experiments.py data/00035_breakfast/00035-00000006.soc --metodo matriz --tecnica todos --b 0.05 --seeds 0,1,2
```

---

## Dependencias principales

El proyecto utiliza principalmente:

- `numpy`, para el manejo de matrices;
- `scipy`, para funciones estadísticas utilizadas en la estrategia de scores latentes;
- `pyscipopt`, para resolver el modelo de programación lineal entera del OBOP.

Las dependencias completas se encuentran en:

```text
requirements.txt
```
