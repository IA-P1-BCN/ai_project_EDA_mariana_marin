"""Genera el JSON que usa la página pública de exploración.

    python scripts/exportar_web.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

import pandas as pd

from limpieza import media_movil  # noqa: E402

REGIONES = ["Noreste", "Medio Oeste", "Sur", "Oeste"]


def main() -> None:
    df = pd.read_csv(RAIZ / "data" / "processed" / "covid_limpio.csv", parse_dates=["fecha"])
    cierre = df[df["fecha"] == df["fecha"].max()].dropna(subset=["muertes_por_100k"])
    foto = [
        {
            "nombre": fila.nombre,
            "region": fila.region,
            "sigla": fila.state,
            "muertes": int(fila.death),
            "tasa": round(float(fila.muertes_por_100k), 1),
            "casos": round(float(fila.casos_por_100k), 1),
            "letalidad": round(float(fila.letalidad_aparente) * 100, 2),
            "poblacion": int(fila.poblacion_2020),
        }
        for fila in cierre.sort_values("muertes_por_100k", ascending=False).itertuples()
    ]

    pais = df.groupby("fecha")["deathIncrease"].sum().sort_index()
    pais_mm7 = media_movil(pais, 7).dropna()
    serie_pais = [
        {"fecha": fecha.strftime("%Y-%m-%d"), "mm7": round(float(valor), 1)}
        for fecha, valor in pais_mm7.items()
    ]

    panel = df[df["region"].isin(REGIONES)]
    poblacion = panel.drop_duplicates("state").groupby("region")["poblacion_2020"].sum()
    diarias = panel.groupby(["fecha", "region"])["deathIncrease"].sum().unstack()
    tasa = diarias.div(poblacion) * 100_000
    tasa_mm7 = tasa.apply(media_movil).dropna(how="all")
    serie_region = {
        region: [
            {"fecha": fecha.strftime("%Y-%m-%d"), "tasa": round(float(fila[region]), 3)}
            for fecha, fila in tasa_mm7.iterrows()
            if pd.notna(fila[region])
        ]
        for region in REGIONES
    }

    datos = {"foto": foto, "pais": serie_pais, "regiones": serie_region}
    destino = RAIZ / "docs" / "datos.js"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("window.DATOS = " + json.dumps(datos, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"Jurisdicciones: {len(foto)}")
    print(f"Guardado en {destino}")


if __name__ == "__main__":
    main()
