"""Consultas del dashboard. No dibujan nada: devuelven tablas."""

from __future__ import annotations

import pandas as pd

REGIONES = ["Noreste", "Medio Oeste", "Sur", "Oeste", "Puerto Rico"]


def preparar(df: pd.DataFrame) -> pd.DataFrame:
    salida = df.copy()
    salida["fecha"] = pd.to_datetime(salida["fecha"])
    return salida


def jurisdicciones(df: pd.DataFrame, regiones: list[str]) -> pd.DataFrame:
    """Una fila por jurisdicción con población, dentro de las regiones elegidas."""
    base = df.dropna(subset=["poblacion_2020"]).drop_duplicates("state")
    if regiones:
        base = base[base["region"].isin(regiones)]
    return base.sort_values("nombre")


def foto(df: pd.DataFrame, regiones: list[str], estados: list[str], hasta: pd.Timestamp) -> pd.DataFrame:
    """Último día disponible, con tasa por habitante, para la selección."""
    sub = df[df["fecha"] <= hasta].dropna(subset=["muertes_por_100k"])
    if regiones:
        sub = sub[sub["region"].isin(regiones)]
    if sub.empty:
        return sub
    cierre = sub["fecha"].max()
    ultimo = sub[sub["fecha"] == cierre]
    if estados:
        ultimo = ultimo[ultimo["state"].isin(estados)]
    return ultimo.sort_values("muertes_por_100k", ascending=False)


def serie_mm7(df: pd.DataFrame, estados: list[str], desde: pd.Timestamp, hasta: pd.Timestamp) -> pd.Series:
    """Media de 7 días de muertes nuevas en la selección."""
    sub = df[(df["fecha"] >= desde) & (df["fecha"] <= hasta)]
    if estados:
        sub = sub[sub["state"].isin(estados)]
    if sub.empty:
        return pd.Series(dtype=float)
    diaria = sub.groupby("fecha")["deathIncrease"].sum().sort_index()
    return diaria.rolling(7, min_periods=7).mean()


def tasa_de_la_foto(ultimo: pd.DataFrame) -> float | None:
    if ultimo.empty or ultimo["poblacion_2020"].sum() == 0:
        return None
    return float(ultimo["death"].sum() / ultimo["poblacion_2020"].sum() * 100_000)
