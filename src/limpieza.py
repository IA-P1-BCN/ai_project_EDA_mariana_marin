"""Limpieza reutilizable del histórico diario del COVID Tracking Project.

Las funciones no borran filas: un valor negativo en un incremento diario es una
corrección del estado, y hace falta conservarlo para que la suma cuadre con el
acumulado.
"""

from __future__ import annotations

import pandas as pd

UMBRAL_NULOS = 0.80

# Metadatos internos del proyecto o columnas vacías que no describen la pandemia.
COLUMNAS_METADATO = [
    "hash",
    "grade",
    "dataQualityGrade",
    "commercialScore",
    "negativeRegularScore",
    "negativeScore",
    "positiveScore",
    "score",
    "lastUpdateEt",
    "dateModified",
    "checkTimeEt",
    "dateChecked",
]

COLUMNAS_INCREMENTO = [
    "positiveIncrease",
    "negativeIncrease",
    "totalTestResultsIncrease",
    "deathIncrease",
    "hospitalizedIncrease",
]

DIAS_SEMANA = {
    "Monday": "lunes",
    "Tuesday": "martes",
    "Wednesday": "miércoles",
    "Thursday": "jueves",
    "Friday": "viernes",
    "Saturday": "sábado",
    "Sunday": "domingo",
}


def fecha_desde_entero(fechas: pd.Series) -> pd.Series:
    """Convierte la fecha AAAAMMDD, que llega como entero, a datetime."""
    return pd.to_datetime(fechas.astype(str), format="%Y%m%d")


def columnas_casi_vacias(df: pd.DataFrame, umbral: float = UMBRAL_NULOS) -> list[str]:
    """Columnas cuya proporción de nulos supera el umbral."""
    if not 0 < umbral < 1:
        raise ValueError("umbral debe estar entre 0 y 1")
    proporcion = df.isna().mean()
    return proporcion[proporcion > umbral].index.tolist()


def columna_duplicada(df: pd.DataFrame, izquierda: str, derecha: str) -> bool:
    """True si, en las filas donde ambas columnas tienen valor, coinciden siempre."""
    ambas = df[izquierda].notna() & df[derecha].notna()
    if ambas.sum() == 0:
        return False
    return bool((df.loc[ambas, izquierda] == df.loc[ambas, derecha]).all())


def limites_iqr(serie: pd.Series, factor: float = 1.5) -> tuple[float, float]:
    """Devuelve las vallas inferior y superior del rango intercuartílico."""
    cuartil_1 = float(serie.quantile(0.25))
    cuartil_3 = float(serie.quantile(0.75))
    iqr = cuartil_3 - cuartil_1
    return cuartil_1 - factor * iqr, cuartil_3 + factor * iqr


def mascara_atipicos(serie: pd.Series, factor: float = 1.5) -> pd.Series:
    inferior, superior = limites_iqr(serie, factor)
    return (serie < inferior) | (serie > superior)


def marcar_correcciones_negativas(
    df: pd.DataFrame, columnas: list[str] | None = None
) -> pd.DataFrame:
    """Añade un indicador por columna de incremento. No modifica ni borra valores."""
    salida = df.copy()
    columnas = columnas or [columna for columna in COLUMNAS_INCREMENTO if columna in df.columns]
    for columna in columnas:
        salida[f"{columna}_es_correccion"] = salida[columna] < 0
    return salida


def tasa_por_100k(numerador: pd.Series, poblacion: pd.Series) -> pd.Series:
    """Tasa por 100.000 habitantes. Población 0 o ausente no se usa como divisor."""
    habitantes = poblacion.replace(0, pd.NA)
    return numerador / habitantes * 100_000


def razon_segura(numerador: pd.Series, denominador: pd.Series) -> pd.Series:
    """División que deja NaN cuando el denominador no es positivo."""
    base = denominador.where(denominador > 0)
    return numerador / base


def media_movil(serie: pd.Series, ventana: int = 7) -> pd.Series:
    """Media móvil. Con menos de `ventana` observaciones previas devuelve NaN."""
    if ventana < 1:
        raise ValueError("ventana debe ser >= 1")
    return serie.rolling(ventana, min_periods=ventana).mean()


def preparar_columnas(
    df: pd.DataFrame, umbral_nulos: float = UMBRAL_NULOS
) -> tuple[pd.DataFrame, dict]:
    """Quita columnas inutilizables y convierte la fecha. Conserva todas las filas."""
    informe = {"metadato": [], "casi_vacias": [], "duplicadas": []}
    salida = df.copy()

    metadato = [columna for columna in COLUMNAS_METADATO if columna in salida.columns]
    informe["metadato"] = metadato
    salida = salida.drop(columns=metadato)

    vacias = [
        columna
        for columna in columnas_casi_vacias(salida, umbral_nulos)
        if columna not in {"date", "state", "fecha"}
    ]
    informe["casi_vacias"] = vacias
    salida = salida.drop(columns=vacias)

    if {"hospitalized", "hospitalizedCumulative"}.issubset(salida.columns):
        if columna_duplicada(salida, "hospitalized", "hospitalizedCumulative"):
            salida = salida.drop(columns=["hospitalized"])
            informe["duplicadas"] = ["hospitalized"]

    if "date" in salida.columns:
        salida["fecha"] = fecha_desde_entero(salida["date"])

    salida = marcar_correcciones_negativas(salida)
    return salida, informe


def anadir_variables(df: pd.DataFrame) -> pd.DataFrame:
    """Crea fechas parciales, tasas por habitante y razones. No imputa nulos."""
    salida = df.copy()
    if "fecha" not in salida.columns:
        salida["fecha"] = fecha_desde_entero(salida["date"])

    salida["anio"] = salida["fecha"].dt.year
    salida["mes"] = salida["fecha"].dt.to_period("M").astype(str)
    salida["dia_semana"] = salida["fecha"].dt.day_name().map(DIAS_SEMANA)

    if "poblacion_2020" in salida.columns:
        pares = {
            "casos_por_100k": "positive",
            "muertes_por_100k": "death",
            "pruebas_por_100k": "totalTestResults",
            "hospitalizados_por_100k": "hospitalizedCurrently",
        }
        for destino, origen in pares.items():
            if origen in salida.columns:
                salida[destino] = tasa_por_100k(salida[origen], salida["poblacion_2020"])

    if {"death", "positive"}.issubset(salida.columns):
        salida["letalidad_aparente"] = razon_segura(salida["death"], salida["positive"])
    if {"positive", "totalTestResults"}.issubset(salida.columns):
        salida["positividad_acumulada"] = razon_segura(
            salida["positive"], salida["totalTestResults"]
        )
    return salida
