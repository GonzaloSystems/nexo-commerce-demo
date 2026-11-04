# Nexo Commerce

[Demo pública](https://gonzalosystems.github.io/nexo-commerce-demo/) de investigación de productos para Amazon y Mercado Libre México.

Seis modelos reales, fotos locales y enlaces de publicación. Precios, valoraciones y contadores públicos observados el 28 de octubre de 2026. Son instantáneas, no un servicio en tiempo real. Amazon: compras del mes pasado cuando se publican; Mercado Libre: acumulados.

Valor orientativo = mínimo del contador público × precio consultado. No es facturación observada ni un mínimo de ingresos históricos.

`estimator.js` ajusta una ley de potencia con referencias observadas de Amazon México en CSV. Sin coeficientes universales, precisión comercial validada ni histórico de ventas inventado. El archivo se procesa en la pestaña. Plantilla: `calibracion.csv`.

Pruebas de cálculo con datos sintéticos: `node --test tests/estimator.test.cjs`.

La extensión es un concepto visual. Sin acceso a cuentas privadas configurado. El backend local opcional está en `backend/`; GitHub Pages sigue sirviendo la muestra estática. Logos e imágenes identifican a sus respectivos productos y titulares; Nexo no está afiliado con sus marcas. Fuentes en `assets/products/FUENTES.txt`.

## Datos por API

[Decisión, requisitos y costes](decision-apis.md). Clientes Keepa y Amazon SP-API, SQLite e interfaz local en [backend/README.md](backend/README.md). Clave guardada solo en el equipo local y conexión Rainforest verificada el 03.11.2026: 48 productos de Amazon México. No se publican claves ni respuestas completas del proveedor. Las llamadas se realizan en el servidor, nunca desde JavaScript público. El estimador anterior se conserva.

Filtros de investigación: categoría, marca, tipo, ASIN/lista, precio, reseñas y BSR. Buscan en el catálogo disponible; no se ha conectado todavía todo Amazon. [Alta y búsqueda SP-API](alta-amazon.md). Pruebas: `node --test tests/filters.test.cjs`.

## Nexo Prisma (03.11.2026)

Diseño azul/rosa con vidrio estriado, landing y panel responsive. Búsqueda nueva por texto/ASIN mediante el servidor local y Rainforest API o SP-API autorizada. La prueba externa requiere clave, nunca incluida en este repositorio. GitHub Pages mantiene el catálogo de muestra; la conexión real se activa en localhost. Detalles en `PROTOCOLO-PROTOTIPO-HOY.txt`.

## Análisis y extensión (04.11.2026)

Diseño Prisma continuo, marca nexo y carrusel accesible de tres productos. Ficha local completa con rankings, contador público de compras, reparto de valoraciones y observaciones de precio/BSR. Ofertas y filtro de vendedores conocidos, sin afirmar censo o ventas privadas. Extensión local Chrome/Edge en `extension/` y `nexo-extension.zip`; pendiente instalación y prueba integral en Chrome. Puente HTTP verificado. Véase EVOLUCION-INTERFAZ.txt.
