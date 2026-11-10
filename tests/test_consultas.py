import pandas as pd
import pytest

from consultas import foto, tasa_de_la_foto


def test_en_el_cierre_nueva_jersey_tiene_la_tasa_mas_alta():
    tabla = pd.read_csv("data/processed/covid_limpio.csv", parse_dates=["fecha"])
    cierre = foto(tabla, [], [], tabla["fecha"].max())
    assert cierre.iloc[0]["state"] == "NJ"
    assert cierre.iloc[0]["muertes_por_100k"] == pytest.approx(265.4, abs=0.1)


def test_la_tasa_de_estados_y_dc_ronda_156():
    tabla = pd.read_csv("data/processed/covid_limpio.csv", parse_dates=["fecha"])
    cierre = foto(tabla, ["Noreste", "Medio Oeste", "Sur", "Oeste"], [], tabla["fecha"].max())
    assert tasa_de_la_foto(cierre) == pytest.approx(155.7, abs=0.2)
