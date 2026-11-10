"""Un comando: descarga, limpia y guarda el histórico listo para el análisis.

Uso, desde la raíz del repositorio:

    python scripts/pipeline.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from cargar import cargar_covid, cargar_poblacion  # noqa: E402
from limpieza import anadir_variables, preparar_columnas  # noqa: E402


def main() -> None:
    crudo = cargar_covid(RAIZ / "data" / "raw" / "covid_states_daily.csv")
    limpio, informe = preparar_columnas(crudo)
    poblacion = cargar_poblacion(RAIZ / "data" / "external" / "nst-est2020-alldata.csv")
    salida = anadir_variables(limpio.merge(poblacion, on="state", how="left"))

    destino = RAIZ / "data" / "processed"
    destino.mkdir(parents=True, exist_ok=True)
    ruta_csv = destino / "covid_limpio.csv"
    salida.to_csv(ruta_csv, index=False)

    informe["filas_entrada"] = int(len(crudo))
    informe["filas_salida"] = int(len(salida))
    informe["columnas_salida"] = int(salida.shape[1])
    informe["sin_poblacion"] = sorted(salida.loc[salida["poblacion_2020"].isna(), "state"].unique())
    (destino / "informe_limpieza.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Filas: {informe['filas_entrada']} -> {informe['filas_salida']} (no se borró ninguna)")
    print(f"Columnas de metadato eliminadas: {len(informe['metadato'])}")
    print(f"Columnas casi vacías eliminadas: {len(informe['casi_vacias'])}")
    print(f"Columnas duplicadas eliminadas: {informe['duplicadas']}")
    print(f"Jurisdicciones sin población del censo: {informe['sin_poblacion']}")
    print(f"Guardado en {ruta_csv}")


if __name__ == "__main__":
    main()
