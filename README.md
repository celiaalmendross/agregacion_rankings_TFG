# Agregación de rankings con empates mediante OBOP

Este repositorio contiene el código desarrollado para un Trabajo Fin de Grado realizado por **Celia Almendros Saelices**.

## Objetivo del proyecto

El proyecto se centra en la agregación de rankings con empates mediante el **Optimal Bucket Order Problem (OBOP)**, un problema cuyo objetivo es obtener un ranking de consenso que permita empates entre elementos.
El código permite construir matrices de precedencias a partir de datasets de rankings, resolver el consenso óptimo mediante programación lineal entera y estudiar el efecto de distintas estrategias de introducción de ruido sobre el consenso final.

Además del consenso centralizado exacto, el proyecto incluye una simulación federada sencilla para analizar cómo cambia el consenso final cuando la información se perturba o se distribuye entre varios clientes.

El objetivo principal es comparar el consenso original obtenido mediante OBOP con los consensos obtenidos tras introducir ruido en los datos o al simular un entorno federado.

Para ello, el proyecto permite:

- cargar datasets de rankings en formato PrefLib;
- construir la matriz de precedencias por pares `C`;
- resolver el OBOP mediante programación lineal entera;
- aplicar distintas estrategias de ruido;
- simular un escenario federado con varios clientes;
- comparar el consenso original y el consenso perturbado mediante distintas métricas.

## Estructura del repositorio
La estructura general del repositorio es la siguiente:´

```text
agregacion_rankings_TFG/
│
├── data/
│   ├── 00004_netflix/
│   ├── 00006_skate/
│   ├── 00035_breakfast/
│   ├── 00068_poland_local_elections/
│   ├── 00071_voter-autrement-in-situ/
│   ├── seleccion_federado_poland/
│   ├── seleccion_federado_breakfast/
│   ├── seleccion_federado_netflix/
│   ├── seleccion_federado_skate/
│   └── README.md
│
├── outputs/
│   ├── baseline/
│   ├── ruido/
│   └── federado/
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
│   │   └── agregacion_federada.py
│   │
│   ├── metricas/
│   │   ├── kendall_tau.py
│   │   └── perdida_calidad.py
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

## Ejecución

Los scripts deben ejecutarse desde la raíz del proyecto, es decir, desde la carpeta donde se encuentran `README.md`, `src/`, `data/` y `outputs/`.

### 1. Ejecución del baseline

El baseline consiste en resolver el OBOP sobre la matriz original, sin introducir ruido.

La ejecución general es:

```bash
python src/run_baseline.py <ruta> [max_datasets]
```

Donde:

- `<ruta>` puede ser un fichero concreto o una carpeta con varios datasets.
- `[max_datasets]` es opcional y permite limitar el número de instancias ejecutadas cuando se pasa una carpeta.
- Si se pasa un fichero concreto, se ejecuta solo ese fichero.
- Si se pasa una carpeta y no se indica `max_datasets`, se ejecutan todos los ficheros de la carpeta.

Ejemplo para ejecutar todas las instancias de una carpeta:

```bash
python src/run_baseline.py data/00068_poland_local_elections
```

Ejemplo para ejecutar solo las 5 primeras instancias de una carpeta:

```bash
python src/run_baseline.py data/00068_poland_local_elections 5
```

Ejemplo para ejecutar un único fichero:

```bash
python src/run_baseline.py data/00023-00000001.toi
```

Los resultados del baseline se guardan en:

```text
outputs/baseline/
```

---

### 2. Ejecución de experimentos con ruido

Los experimentos con ruido consisten en perturbar los datos de entrada, resolver de nuevo el OBOP y comparar el consenso perturbado con el consenso original.

La ejecución general es:

```bash
python src/run_ruido_experiments.py <ruta> [max_datasets] [opciones]
```

Donde:

- `<ruta>` puede ser un fichero concreto o una carpeta con varios datasets.
- `[max_datasets]` es opcional y limita el número de instancias si se pasa una carpeta.
- `[opciones]` permite seleccionar el método de ruido, la técnica, las semillas y los parámetros de ruido.

Si no se indican opciones adicionales, el script ejecuta todas las configuraciones disponibles por defecto.

## Opciones disponibles para los experimentos con ruido

| Parámetro | Descripción | Valor por defecto |
|---|---|---|
| `--metodo` | Familia de ruido a ejecutar: `matriz`, `rankings`, `scores` o `todos` | `todos` |
| `--tecnica` | Técnica o técnicas concretas separadas por coma | Todas las del método elegido |
| `--seeds` | Semillas aleatorias separadas por coma | `0,1,2` |
| `--b` | Valores de intensidad de ruido separados por coma | `0.01,0.05,0.10` |

---

## Métodos de ruido implementados

El proyecto incluye tres familias de ruido:

- ruido sobre la matriz de precedencias;
- ruido sobre rankings individuales;
- ruido sobre scores latentes.

### Ruido sobre matriz

Este método introduce ruido directamente sobre la matriz de precedencias por pares `C`.

Técnicas disponibles:

| Técnica | Descripción |
|---|---|
| `todos` | Introduce ruido en todos los pares de la matriz |
| `aleatoria` | Introduce ruido en una parte aleatoria de los pares |
| `cerca_empate` | Introduce ruido únicamente en pares cercanos al empate |

Ejemplo con una técnica concreta:

```bash
python src/run_ruido_experiments.py data/00068_poland_local_elections 5 --metodo matriz --tecnica cerca_empate --b 0.01,0.05,0.10
```

### Ruido sobre rankings

Este método introduce ruido sobre los rankings individuales antes de construir la matriz de precedencias perturbada.

Técnicas disponibles:

| Técnica | Descripción |
|---|---|
| `intercambio` | Intercambia elementos dentro de los rankings |
| `movimiento` | Mueve elementos dentro del ranking |
| `empate` | Crea, elimina o modifica empates |
| `local` | Aplica modificaciones locales en los rankings |

Ejemplo con una técnica concreta:

```bash
python src/run_ruido_experiments.py data/00068_poland_local_elections 5 --metodo rankings --tecnica movimiento
```

### Ruido sobre scores latentes

Este método transforma la matriz de precedencias en una representación basada en scores latentes, introduce ruido sobre dichos scores y reconstruye una matriz perturbada.

Técnicas disponibles:

| Técnica | Descripción |
|---|---|
| `logistic` | Reconstruye la matriz perturbada usando una función logística |
| `probit` | Reconstruye la matriz perturbada usando una función probit |

Ejemplo con una técnica concreta:

```bash
python src/run_ruido_experiments.py data/00068_poland_local_elections 5 --metodo scores --tecnica logistic
```

---

### 3. Experimentos federados
La simulación federada divide los rankings de cada instancia entre varios clientes. Después se estudian dos variantes:

- Cada cliente construye localmente su matriz de precedencias, la perturba y envía la matriz perturbada al servidor.
- Cada cliente perturba sus rankings y envía los rankings perturbados al servidor.

El servidor agrega la información recibida, reconstruye una matriz global y resuelve el OBOP.

La ejecución general es:

```bash
python src/run_federado_experiments.py <ruta> [max_datasets] [opciones]
```

## Opciones disponibles para los experimentos con ruido

| Parámetro | Descripción | Valor por defecto |
|---|---|---|
| `--modo` | Variable federada: `matrices`, `rankings`o `todos` | `todos` |
| `--tecnica` | Técnica o técnicas concretas separadas por coma | Todas las del método elegido |
| `--clientes` | Número de clientes simulados | `3` |
| `--seeds` | Semillas aleatorias separadas por coma | `0,1,2` |
| `--b` | Valores de intensidad de ruido separados por coma | `0.01,0.05,0.10` |

Ejemplo con modo "matrices":

```bash
python src/run_federado_experiments.py data/seleccion_federado_poland --modo matrices --tecnica cerca_empate --clientes 2,3,5 --seeds 0,1,2 --b 0,0.2
```

## Carpeta `outputs`

La carpeta `outputs/` almacena los resultados generados por las ejecuciones del proyecto.

Su estructura es:

```text
outputs/
├── baseline/
├── ruido/
└── federado/

```

### `outputs/baseline/`

Esta carpeta contiene los resultados de las ejecuciones sin ruido. 
Los ficheros generados en esta carpeta incluyen información como:

- nombre de la instancia;
- tipo de dataset;
- número de elementos;
- número de rankings;
- valor objetivo del OBOP;
- número de buckets del consenso;
- tiempo de ejecución;
- bucket order obtenido.

### `outputs/ruido/`

Esta carpeta contiene los resultados de los experimentos en los que se introduce ruido en los datos.

Los ficheros generados en esta carpeta incluyen información como:

- nombre de la instancia;
- tipo de dataset;
- número de elementos;
- número de rankings;
- método de ruido utilizado;
- técnica aplicada;
- parámetros de ruido;
- semilla utilizada;
- valor objetivo original;
- valor objetivo con ruido;
- Kendall tau entre el consenso original y el consenso perturbado;
- pérdida respecto a la matriz original;
- número de buckets del consenso original;
- número de buckets del consenso perturbado;
- tiempo de ejecución;
- bucket order original;
- bucket order obtenido tras introducir ruido.

### `outputs/federado/`

Esta carpeta contiene los resultados de los experimentos de la simulación del entorno federado.

Los ficheros generados en esta carpeta incluyen información como:

- nombre de la instancia;
- tipo de dataset;
- número de elementos;
- número de rankings;
- número de clientes;
- modo 
- técnica aplicada;
- parámetros de ruido;
- semilla utilizada;
- valor objetivo original;
- valor objetivo con entorno federado;
- Kendall tau entre el consenso original y el consenso perturbado;
- pérdida respecto a la matriz original;
- número de buckets del consenso original;
- número de buckets del consenso federado;
- tiempo de ejecución;
- bucket order original;
- bucket order obtenido en entorno federado.

