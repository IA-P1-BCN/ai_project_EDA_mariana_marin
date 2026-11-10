# Calidad de los datos

Histórico diario del COVID Tracking Project, descargado de `https://api.covidtracking.com/v1/states/daily.json`, y población `NST-EST2020-alldata` del U.S. Census Bureau (estimación a 1 de julio de 2020). Corte del archivo de casos: **7 de marzo de 2021**. A partir de esa fecha el proyecto dejó de actualizar.

20.780 filas, 56 columnas, 56 jurisdicciones. No hay filas duplicadas ni pares estado-fecha repetidos. No se eliminó ninguna fila.

## Qué faltaba

Trece columnas superan el 80% de nulos: pruebas de anticuerpos y de antígenos, personas testadas con esas técnicas, ventiladores acumulados, UCI acumulada, altas hospitalarias y pruebas pendientes. No dan para comparar estados. Se eliminan. Imputarlas con una mediana crearía cifras que ningún estado publicó.

`grade` llega vacío y `dataQualityGrade` está vacío del todo. `score` y el resto de puntuaciones internas valen siempre cero. El hash y las marcas de tiempo de la descarga (`lastUpdateEt`, `dateModified`, `checkTimeEt`, `dateChecked`) identifican el fichero, no la pandemia. Se eliminan como metadato: 12 columnas.

`hospitalized` es una copia exacta de `hospitalizedCumulative`. Se conserva la de nombre explícito.

## Qué se corrigió, y qué se dejó como está

`date` venía como entero (`20200313`). Pasa a fecha. El `astype(str)` evita el aviso de pandas 3.

Los incrementos diarios traen valores negativos: 73 en muertes, y también en casos, pruebas y hospitalizaciones. Son correcciones de los estados sobre días anteriores. La suma de `deathIncrease`, negativos incluidos, es **515.151**, idéntica a las muertes acumuladas del último día. Si se pusieran a cero, el total dejaría de cuadrar. Se quedan, con una columna que los marca (`deathIncrease_es_correccion` y las equivalentes).

La suma de `positiveIncrease` se queda **96 casos** por debajo del acumulado de `positive` el 7 de marzo (28.756.393 frente a 28.756.489). El desfase está repartido en pocos estados y el mayor es California (53). Queda documentado y no se reparte a mano.

`death` y `positive` tienen huecos en algunos días del principio de la serie. No se rellenan con cero: un cero diría «ese día no hubo muertes». El 7 de marzo, el día de la foto, las jurisdicciones con población tienen las dos cifras.

`hospitalizedCurrently` falta en el 16,6% de las filas y en jurisdicciones enteras durante tramos largos. Florida no la informa el 40,3% de sus días. Samoa Americana e Islas Marianas del Norte no la informan nunca. No se imputa. La cobertura es casi nula en los dos primeros meses y ronda el 95% en los últimos sesenta días. Por eso la suma nacional de hospitalizados de abril de 2020 no es comparable con la de enero de 2021.

El rango intercuartílico marca 2.208 filas de `deathIncrease` como atípicas (valla superior en 60 muertes diarias de un estado). Son los días de las olas y los días en que un estado vuelca retrasos. No se eliminan.

`totalTestResults` mezcla cuatro definiciones (`totalTestsViral`, encuentros de prueba, positivos más negativos, personas testadas). Una tasa de pruebas por habitante se puede calcular, y no se puede leer como si todos los estados contaran lo mismo.

## Segunda fuente

El cruce es por las siglas del estado. La población permite las tasas por 100.000. Samoa Americana, Guam, las Islas Marianas del Norte y las Islas Vírgenes no están en el archivo del censo que se usó. Entre las cuatro suman 160 muertes en este histórico: no mueven el total y quedan fuera de las tasas. Puerto Rico sí tiene población (tasa de 65,3 por 100.000) y el censo no lo mete en ninguna de las cuatro regiones; en los gráficos regionales se muestra aparte o no entra en el diagrama de caja, donde un solo punto no resume una distribución.

El Distrito de Columbia va con el Sur porque así lo publica el Census Bureau.

## Qué queda pendiente

- No hay edad, y sin edad la diferencia de letalidad aparente entre estados (Utah 0,5%, Nueva Jersey 2,9% de los casos detectados) no tiene explicación dentro de este archivo.
- El archivo se corta el 7 de marzo de 2021. Enero y febrero de ese año están completos; marzo, no. Cualquier total de «2021» en la tabla dinámica es un trimestre incompleto.
- La positividad usa el total de pruebas con definiciones mezcladas. Sirve para ver el cambio de régimen (cerca del 20% a mediados de abril de 2020, cerca del 4% al cierre) y no como un porcentaje de laboratorio.
- No se construyó un dashboard. El HTML interactivo de `reports/figuras/muertes_por_100k.html` cubre la exploración estado a estado.
