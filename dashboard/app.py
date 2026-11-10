"""Dashboard para explorar el histórico sin leer el notebook.

Desde la raíz del repositorio:

    streamlit run dashboard/app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from consultas import REGIONES, foto, jurisdicciones, preparar, serie_mm7, tasa_de_la_foto

RAIZ = Path(__file__).resolve().parents[1]
CSV = RAIZ / "data" / "processed" / "covid_limpio.csv"

st.set_page_config(page_title="COVID-19 en Estados Unidos", layout="wide")


@st.cache_data
def cargar() -> pd.DataFrame:
    if not CSV.exists():
        return pd.DataFrame()
    return preparar(pd.read_csv(CSV))


df = cargar()
if df.empty:
    st.error("No está el CSV limpio. Desde la raíz del proyecto ejecuta: python scripts/pipeline.py")
    st.stop()

fecha_min = df["fecha"].min().date()
fecha_max = df["fecha"].max().date()

st.title("COVID-19 en Estados Unidos")
st.caption(
    f"Partes diarios del {fecha_min.strftime('%d/%m/%Y')} al {fecha_max.strftime('%d/%m/%Y')}. "
    "La tasa está en muertes por 100.000 habitantes."
)

with st.sidebar:
    st.header("Filtros")
    regiones = st.multiselect("Región", REGIONES, default=["Noreste", "Medio Oeste", "Sur", "Oeste"])
    opciones = jurisdicciones(df, regiones)
    estados = st.multiselect(
        "Jurisdicción",
        options=opciones["state"].tolist(),
        format_func=lambda sigla: opciones.loc[opciones["state"] == sigla, "nombre"].iloc[0],
    )
    desde, hasta = st.slider(
        "Periodo",
        min_value=fecha_min,
        max_value=fecha_max,
        value=(fecha_min, fecha_max),
        format="DD/MM/YYYY",
    )

def miles(valor: float) -> str:
    return f"{valor:,.0f}".replace(",", ".")


def coma(valor: float) -> str:
    return f"{valor:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")


if not regiones:
    st.warning("Elige al menos una región.")
    st.stop()

elegidos = estados or opciones["state"].tolist()
cierre = foto(df, regiones, elegidos, pd.Timestamp(hasta))
serie = serie_mm7(df, elegidos, pd.Timestamp(desde), pd.Timestamp(hasta))
tasa = tasa_de_la_foto(cierre)

col1, col2, col3 = st.columns(3)
col1.metric("Muertes acumuladas", miles(cierre["death"].sum()) if not cierre.empty else "—")
col2.metric("Por 100.000 habitantes", coma(tasa) if tasa is not None else "—")
col3.metric("Jurisdicciones", f"{len(cierre)}")

if not cierre.empty:
    lider = cierre.iloc[0]
    st.info(
        f"En esta selección, {lider['nombre']} tiene la tasa más alta: "
        f"{coma(lider['muertes_por_100k'])} muertes por 100.000 habitantes "
        f"({miles(lider['death'])} muertes)."
    )

izq, der = st.columns(2)
with izq:
    st.subheader("Muertes nuevas, media de 7 días")
    if serie.dropna().empty:
        st.write("No hay suficientes días en el periodo para una media de 7 días.")
    else:
        grafico = serie.dropna().rename("muertes").reset_index()
        figura = px.line(
            grafico,
            x="fecha",
            y="muertes",
            labels={"fecha": "Fecha", "muertes": "Muertes nuevas"},
            template="simple_white",
        )
        figura.update_traces(line_color="#9f1239")
        figura.update_layout(margin={"l": 10, "r": 10, "t": 10, "b": 10}, height=420)
        st.plotly_chart(figura, use_container_width=True)

with der:
    st.subheader("Tasa al cierre del periodo")
    if cierre.empty:
        st.write("La selección no tiene datos de población.")
    else:
        ranking = cierre.head(12).sort_values("muertes_por_100k")
        barras = px.bar(
            ranking,
            x="muertes_por_100k",
            y="nombre",
            orientation="h",
            color="region",
            labels={"muertes_por_100k": "Muertes por 100.000", "nombre": "", "region": "Región"},
            template="simple_white",
            color_discrete_map={
                "Noreste": "#b45309",
                "Medio Oeste": "#0369a1",
                "Sur": "#be123c",
                "Oeste": "#0f766e",
                "Puerto Rico": "#6b7280",
            },
        )
        barras.update_layout(margin={"l": 10, "r": 10, "t": 10, "b": 10}, height=420)
        st.plotly_chart(barras, use_container_width=True)

st.caption(
    "Los totales sin dividir por población ordenan los estados por tamaño. "
    "Domingo y lunes publican menos muertes por retraso de reporte: por eso la línea es una media de 7 días."
)
