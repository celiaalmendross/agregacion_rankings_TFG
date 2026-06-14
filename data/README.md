# Datasets

Esta carpeta contiene los conjuntos de datos utilizados en los experimentos del proyecto.

Los datos proceden de PrefLib y contienen perfiles de preferencias en distintos formatos de rankings, incluyendo rankings completos, rankings incompletos y rankings con empates.

## Colecciones incluidas

- `00006_skate/`: clasificaciones deportivas de competiciones de patinaje.
- `00035_breakfast/`: preferencias individuales sobre opciones de desayuno.
- `00068_poland_local_elections/`: preferencias electorales en elecciones locales polacas.
- `00071_voter-autrement-in-situ/`: datos de votación del proyecto Voter Autrement.

## Instancias seleccionadas

Aunque las carpetas pueden contener más ficheros, la experimentación final se ha realizado sobre cuatro instancias concretas:

| Colección | Instancia | Formato |
|---|---|---|
| `00006_skate/` | `00006-00000040.toc` | `.toc` |
| `00035_breakfast/` | `00035-00000006.soc` | `.soc` |
| `00068_poland_local_elections/` | `00068-00000301.soi` | `.soi` |
| `00071_voter-autrement-in-situ/` | `00071-00000033.toi` | `.toi` |

## Formatos utilizados

El proyecto trabaja principalmente con ficheros de PrefLib:

- `.soc`: rankings completos sin empates.
- `.soi`: rankings incompletos sin empates.
- `.toc`: rankings completos con empates.
- `.toi`: rankings incompletos con empates.

Estos ficheros se transforman internamente en una matriz de precedencias por pares `C`, que se utiliza como entrada del problema OBOP.

## Nota sobre los datos

Los datasets no son datos generados por el proyecto, sino conjuntos procedentes de PrefLib. Se incluyen únicamente con fines experimentales y de reproducibilidad del Trabajo Fin de Grado.
