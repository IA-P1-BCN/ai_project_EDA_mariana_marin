"""Descarga y lectura de las dos fuentes del análisis."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

URL_COVID = "https://api.covidtracking.com/v1/states/daily.json"
URL_CENSO = (
    "https://www2.census.gov/programs-surveys/popest/datasets/"
    "2010-2020/state/totals/nst-est2020-alldata.csv"
)

# Códigos FIPS de estado del censo de EE. UU.
FIPS_A_SIGLA = {
    1: "AL",
    2: "AK",
    4: "AZ",
    5: "AR",
    6: "CA",
    8: "CO",
    9: "CT",
    10: "DE",
    11: "DC",
    12: "FL",
    13: "GA",
    15: "HI",
    16: "ID",
    17: "IL",
    18: "IN",
    19: "IA",
    20: "KS",
    21: "KY",
    22: "LA",
    23: "ME",
    24: "MD",
    25: "MA",
    26: "MI",
    27: "MN",
    28: "MS",
    29: "MO",
    30: "MT",
    31: "NE",
    32: "NV",
    33: "NH",
    34: "NJ",
    35: "NM",
    36: "NY",
    37: "NC",
    38: "ND",
    39: "OH",
    40: "OK",
    41: "OR",
    42: "PA",
    44: "RI",
    45: "SC",
    46: "SD",
    47: "TN",
    48: "TX",
    49: "UT",
    50: "VT",
    51: "VA",
    53: "WA",
    54: "WV",
    55: "WI",
    56: "WY",
    72: "PR",
}

NOMBRE_ES = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "DC": "Distrito de Columbia",
    "FL": "Florida",
    "GA": "Georgia",
    "HI": "Hawái",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Luisiana",
    "ME": "Maine",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Míchigan",
    "MN": "Minnesota",
    "MS": "Misisipi",
    "MO": "Misuri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "Nuevo Hampshire",
    "NJ": "Nueva Jersey",
    "NM": "Nuevo México",
    "NY": "Nueva York",
    "NC": "Carolina del Norte",
    "ND": "Dakota del Norte",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregón",
    "PA": "Pensilvania",
    "RI": "Rhode Island",
    "SC": "Carolina del Sur",
    "SD": "Dakota del Sur",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "Virginia Occidental",
    "WI": "Wisconsin",
    "WY": "Wyoming",
    "PR": "Puerto Rico",
}

REGIONES = {
    "1": "Noreste",
    "2": "Medio Oeste",
    "3": "Sur",
    "4": "Oeste",
}


def _descargar(url: str, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    respuesta = requests.get(url, timeout=120)
    respuesta.raise_for_status()
    destino.write_bytes(respuesta.content)


def cargar_covid(ruta_csv: Path, url: str = URL_COVID) -> pd.DataFrame:
    """Lee el CSV local o, si no existe, descarga el JSON de la API y lo guarda."""
    if not ruta_csv.exists():
        respuesta = requests.get(url, timeout=120)
        respuesta.raise_for_status()
        tabla = pd.DataFrame(respuesta.json())
        ruta_csv.parent.mkdir(parents=True, exist_ok=True)
        tabla.to_csv(ruta_csv, index=False)
    else:
        tabla = pd.read_csv(ruta_csv)
    # Un campo vacío ("") y un nulo dicen lo mismo: no hay dato.
    for columna in tabla.select_dtypes(include="object").columns:
        tabla[columna] = tabla[columna].replace(r"^\s*$", pd.NA, regex=True)
    return tabla


def preparar_poblacion(censo: pd.DataFrame) -> pd.DataFrame:
    """Quédate con estados, DC y Puerto Rico, y traduce región y nombre."""
    estados = censo.loc[
        censo["SUMLEV"] == 40, ["STATE", "NAME", "REGION", "POPESTIMATE2020"]
    ].copy()
    estados["state"] = estados["STATE"].map(FIPS_A_SIGLA)
    if estados["state"].isna().any():
        faltan = estados.loc[estados["state"].isna(), "NAME"].tolist()
        raise ValueError(f"FIPS sin sigla: {faltan}")
    region = estados["REGION"].astype(str).str.replace(r"\.0$", "", regex=True)
    estados["region"] = region.map(REGIONES).fillna("Puerto Rico")
    estados["nombre"] = estados["state"].map(NOMBRE_ES)
    return estados[["state", "nombre", "region", "POPESTIMATE2020"]].rename(
        columns={"POPESTIMATE2020": "poblacion_2020"}
    )


def cargar_poblacion(ruta_csv: Path, url: str = URL_CENSO) -> pd.DataFrame:
    """Estimación de población a 1 de julio de 2020 (U.S. Census Bureau, NST-EST2020)."""
    if not ruta_csv.exists():
        _descargar(url, ruta_csv)
    censo = pd.read_csv(ruta_csv, encoding="latin1")
    return preparar_poblacion(censo)
