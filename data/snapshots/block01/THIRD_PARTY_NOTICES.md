# Atribución de fuentes externas

Las tablas contienen estadísticas agregadas extraídas de INE (IPV, IPVA e IPC)
y MIVAU (tasación, transacciones y SERPAVI). Se conserva el concepto original,
la URL y la huella del archivo fuente en `source_manifest.json`.
La licencia MIT del proyecto cubre el código propio; no reemplaza los términos
de reutilización de las fuentes estadísticas.

- INE: https://www.ine.es/aviso_legal
- MIVAU: https://www.mivau.gob.es/ y enlaces originales del manifiesto.
- Senado: hechos de nombramientos y adscripción de presidencias, con referencias
  a los dosieres oficiales. No se republica su contenido completo.
- CartoCiudad / Instituto Geográfico Nacional: coordenadas de una selección de
  municipios y códigos territoriales; respuestas verificadas individualmente.
  https://www.cartociudad.es/portal/

## Geometrías

Derivadas de `spain-communities.geojson` y `spain-provinces.geojson` de
Code for Germany / Click That 'Hood, con simplificación de 0,012 grados.
https://github.com/codeforgermany/click_that_hood

Los atributos señalan una actualización de 2014. Se utilizan exclusivamente
como cartografía ilustrativa, sin cálculos de superficie ni delimitación actual.
La copia de la licencia MIT del proyecto original acompaña estos archivos en
`BOUNDARIES_LICENSE.txt`. Se conserva el aviso de copyright íntegro.
