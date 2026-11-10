import pandas as pd
import pytest

from cargar import preparar_poblacion
from limpieza import (
    anadir_variables,
    columna_duplicada,
    columnas_casi_vacias,
    fecha_desde_entero,
    limites_iqr,
    marcar_correcciones_negativas,
    mascara_atipicos,
    media_movil,
    preparar_columnas,
    razon_segura,
    tasa_por_100k,
)


def test_fecha_desde_entero():
    fechas = fecha_desde_entero(pd.Series([20200313, 20210101]))
    assert fechas.iloc[0] == pd.Timestamp("2020-03-13")
    assert fechas.iloc[1] == pd.Timestamp("2021-01-01")


def test_columnas_casi_vacias_respeta_el_umbral():
    tabla = pd.DataFrame(
        {"a": [1, None, None, None, None], "b": [1, 2, 3, 4, 5]}
    )
    assert columnas_casi_vacias(tabla, 0.5) == ["a"]
    assert columnas_casi_vacias(tabla, 0.9) == []


def test_umbral_fuera_de_rango():
    with pytest.raises(ValueError):
        columnas_casi_vacias(pd.DataFrame({"a": [1]}), 1)


def test_columna_duplicada_ignora_nulos():
    tabla = pd.DataFrame({"a": [1, 2, None], "b": [1, 2, 9]})
    assert columna_duplicada(tabla, "a", "b")
    distinta = pd.DataFrame({"a": [1, 2], "b": [1, 3]})
    assert not columna_duplicada(distinta, "a", "b")


def test_tasa_por_100k_y_poblacion_cero():
    tasa = tasa_por_100k(pd.Series([10, 10]), pd.Series([1000, 0]))
    assert tasa.iloc[0] == pytest.approx(1000)
    assert pd.isna(tasa.iloc[1])


def test_razon_segura_no_divide_entre_cero_ni_negativo():
    razon = razon_segura(pd.Series([1, 2, 3]), pd.Series([0, 4, -2]))
    assert pd.isna(razon.iloc[0])
    assert razon.iloc[1] == pytest.approx(0.5)
    assert pd.isna(razon.iloc[2])


def test_correcciones_negativas_no_borran_filas_ni_valores():
    tabla = pd.DataFrame({"deathIncrease": [5, -2, 0]})
    salida = marcar_correcciones_negativas(tabla, ["deathIncrease"])
    assert len(salida) == 3
    assert salida["deathIncrease"].tolist() == [5, -2, 0]
    assert salida["deathIncrease_es_correccion"].tolist() == [False, True, False]


def test_media_movil_de_siete_dias():
    serie = pd.Series([1, 1, 1, 1, 1, 1, 7], dtype=float)
    media = media_movil(serie, 7)
    assert pd.isna(media.iloc[5])
    assert media.iloc[6] == pytest.approx(13 / 7)


def test_limites_iqr():
    serie = pd.Series([1, 2, 3, 4, 5, 6, 7, 100])
    inferior, superior = limites_iqr(serie)
    assert inferior < superior
    assert bool(mascara_atipicos(serie).iloc[-1])


def test_preparar_columnas_conserva_filas_y_documenta_los_descartes():
    tabla = pd.DataFrame(
        {
            "date": [20200301, 20200302],
            "state": ["NY", "NY"],
            "hospitalized": [10, 12],
            "hospitalizedCumulative": [10, 12],
            "deathIncrease": [1, -1],
            "casi_vacia": [None, None],
            "hash": ["x", "y"],
            "positive": [100, 110],
            "death": [1, 2],
        }
    )
    salida, informe = preparar_columnas(tabla, umbral_nulos=0.5)
    assert len(salida) == 2
    assert "hash" not in salida.columns
    assert "hospitalized" not in salida.columns
    assert "hospitalizedCumulative" in salida.columns
    assert "casi_vacia" not in salida.columns
    assert salida["fecha"].iloc[0] == pd.Timestamp("2020-03-01")
    assert salida["deathIncrease"].tolist() == [1, -1]
    assert informe["duplicadas"] == ["hospitalized"]
    assert "casi_vacia" in informe["casi_vacias"]
    assert "hash" in informe["metadato"]


def test_anadir_variables_crea_tasa_mes_y_dia():
    tabla = pd.DataFrame(
        {
            "date": [20200302],
            "positive": [50],
            "death": [5],
            "totalTestResults": [200],
            "hospitalizedCurrently": [4],
            "poblacion_2020": [100_000],
        }
    )
    salida = anadir_variables(tabla)
    assert salida["mes"].iloc[0] == "2020-03"
    assert salida["dia_semana"].iloc[0] == "lunes"
    assert salida["muertes_por_100k"].iloc[0] == pytest.approx(5)
    assert salida["letalidad_aparente"].iloc[0] == pytest.approx(0.1)
    assert salida["positividad_acumulada"].iloc[0] == pytest.approx(0.25)


def test_preparar_poblacion_traduce_nueva_jersey_y_puerto_rico():
    censo = pd.DataFrame(
        {
            "SUMLEV": [10, 40, 40],
            "STATE": [0, 34, 72],
            "NAME": ["United States", "New Jersey", "Puerto Rico"],
            "REGION": ["0", "1", "X"],
            "POPESTIMATE2020": [100, 8_882_371, 3_159_343],
        }
    )
    salida = preparar_poblacion(censo)
    assert salida["state"].tolist() == ["NJ", "PR"]
    nueva_jersey = salida.loc[salida["state"] == "NJ"].iloc[0]
    assert nueva_jersey["nombre"] == "Nueva Jersey"
    assert nueva_jersey["region"] == "Noreste"
    assert salida.loc[salida["state"] == "PR", "region"].item() == "Puerto Rico"
