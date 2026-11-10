# COVID-19 en Estados Unidos: análisis exploratorio

Repositorio de la entrega: https://github.com/marianamarinf/ai_project_EDA

Histórico diario del [COVID Tracking Project](https://covidtracking.com/) (13 de enero de 2020 – 7 de marzo de 2021), cruzado con la población estatal del censo de EE. UU. a 1 de julio de 2020.

El archivo tiene 20.780 filas y 56 columnas: un parte por jurisdicción y día. California encabeza las muertes acumuladas (54.124) y no entra en las diez jurisdicciones con más muertes por habitante. Nueva Jersey sí: 265,4 por cada 100.000. Enero de 2021 fue el mes con más muertes del país; en el Noreste, el pico diario por habitante llegó el 16 de abril de 2020.

El informe para quien no va a leer el código está en [`reports/informe_ejecutivo.md`](reports/informe_ejecutivo.md).

## De dónde salen los datos

| Archivo | Fuente |
| --- | --- |
| `data/raw/covid_states_daily.csv` | API `https://api.covidtracking.com/v1/states/daily.json`. Se descarga una vez y luego se lee del disco. |
| `data/external/nst-est2020-alldata.csv` | U.S. Census Bureau, estimación de población a 1 de julio de 2020 (`NST-EST2020-alldata`). |

Los dos CSV ya están en el repositorio. Si faltan, `scripts/pipeline.py` los vuelve a pedir.

## Instalación

Hace falta Python 3.10 o superior.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Cómo ejecutar el notebook

Desde la raíz del proyecto, con el entorno activado:

```bash
jupyter notebook notebooks/eda_covid_usa.ipynb
```

El notebook se puede abrir también desde `notebooks/`: localiza la raíz del proyecto solo. Hay que ejecutarlo de arriba abajo. Las figuras quedan en `reports/figuras/`.

## Pipeline y tests

```bash
python scripts/pipeline.py
pytest
```

El pipeline limpia, cruza la población, crea las tasas y guarda `data/processed/covid_limpio.csv`. No borra filas. Los tests cubren la conversión de fechas, el descarte de columnas, las tasas por 100.000 y el trato de los incrementos negativos.

## Estructura

```
notebooks/eda_covid_usa.ipynb   análisis, con texto entre el código
src/limpieza.py                 funciones de limpieza y variables nuevas
src/cargar.py                   descarga y lectura de las dos fuentes
scripts/pipeline.py             mismo recorrido, un comando
tests/test_limpieza.py          pruebas de esas funciones
reports/informe_ejecutivo.md    conclusiones para un público no técnico
reports/calidad_datos.md        qué faltaba, qué se corrigió, qué queda abierto
reports/figuras/                gráficos del notebook
```

## Cómo está subido

`main` es la entrega integrada. El trabajo entra por ramas, cada una con un pull request:

| Rama | Qué entra |
| --- | --- |
| `feat/carga-y-limpieza` | CSV de las dos fuentes, funciones de carga y limpieza, tests y pipeline |
| `feat/analisis-exploratorio` | Notebook del EDA, ejecutable de arriba abajo |
| `docs/informe` | Informe ejecutivo, calidad de los datos, figuras y este README |

No se sube el entorno virtual (`.venv`). Quien clone el repo lo crea con las instrucciones de instalación.

## Qué cubre esta entrega

El notebook recorre el nivel esencial, el medio y el avanzado del enunciado: estructura, nulos, tipos, atípicos, `groupby` y tabla dinámica, variables nuevas, correlación, series temporales, tasas por habitante, segunda fuente, datos de mala calidad, escala logarítmica, media móvil, comparación por región, Plotly y funciones reutilizables.

Además hay tests, un pipeline de un comando y un informe de calidad. No hay dashboard.
