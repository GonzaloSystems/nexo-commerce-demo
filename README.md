# Nexo Commerce

[Demo pública](https://gonzalosystems.github.io/nexo-commerce-demo/) de investigación de productos para Amazon y Mercado Libre México.

Seis modelos reales, fotos locales y enlaces de publicación. Precios, valoraciones y contadores públicos observados el 28 de octubre de 2026. Son instantáneas, no un servicio en tiempo real. Amazon: compras del mes pasado cuando se publican; Mercado Libre: acumulados.

Valor orientativo = mínimo del contador público × precio consultado. No es facturación observada ni un mínimo de ingresos históricos.

`estimator.js` ajusta una ley de potencia con referencias observadas de Amazon México en CSV. Sin coeficientes universales, precisión comercial validada ni histórico de ventas inventado. El archivo se procesa en la pestaña. Plantilla: `calibracion.csv`.

Pruebas de cálculo con datos sintéticos: `node --test tests/estimator.test.cjs`.

La extensión es un concepto visual. Sin acceso a cuentas privadas configurado. El backend local opcional está en `backend/`; GitHub Pages sigue sirviendo la muestra estática. Logos e imágenes identifican a sus respectivos productos y titulares; Nexo no está afiliado con sus marcas. Fuentes en `assets/products/FUENTES.txt`.

## Datos por API

[Decisión, requisitos y costes](decision-apis.md). Clientes Keepa y Amazon SP-API, SQLite e interfaz local en [backend/README.md](backend/README.md). Sin credenciales ni productos recibidos por API hasta ahora. Las llamadas se realizan en el servidor, nunca desde JavaScript público. El estimador anterior se conserva.
