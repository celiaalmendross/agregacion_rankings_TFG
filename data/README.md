# Datasets

Esta carpeta contiene los conjuntos de datos utilizados en los experimentos del proyecto.

Los datos proceden de PrefLib y contienen perfiles de preferencias en distintos formatos de rankings, incluyendo rankings completos, rankings incompletos y rankings con empates.

## Conjuntos incluidos

- `00004_netflix/`: preferencias de usuarios en recomendación de películas.
- `00006_skate/`: clasificaciones deportivas de competiciones de patinaje.
- `00035_breakfast/`: preferencias individuales sobre opciones de desayuno.
- `00068_poland_local_elections/`: preferencias electorales en elecciones locales polacas.
- `00071_voter-autrement-in-situ/`: datos de votación del proyecto Voter Autrement.
- `00023_takoma_park/`: elección municipal de Takoma Park.

## Formatos utilizados

El proyecto trabaja principalmente con ficheros de PrefLib:

- `.soc`: rankings completos sin empates.
- `.soi`: rankings incompletos sin empates.
- `.toc`: rankings completos con empates.
- `.toi`: rankings incompletos con empates.

Estos ficheros se transforman internamente en una matriz de precedencias por pares `C`, que se utiliza como entrada del problema OBOP.

## Nota sobre los datos

Los datasets no son datos generados por el proyecto, sino conjuntos procedentes de PrefLib. Se incluyen únicamente con fines experimentales y de reproducibilidad del Trabajo Fin de Grado.

## Colecciones para el entorno federado
Las carpetas seleccion_federado_[instancia]/ contienen los dataset utilizados para las pruebas de la simulación federada. 