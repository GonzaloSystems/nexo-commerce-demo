# Nexo: decisión de adquisición por API

Investigación y estado comprobado: 28 de octubre de 2026. Alcance: Amazon México. Mercado Libre y el trabajo anterior se conservan; estas APIs no cubren Mercado Libre.

## Decisión

**Priorizar SP-API para catálogo y ofertas actuales cuando podamos autorizar nuestra aplicación con un vendedor. Usar Keepa como complemento de históricos; si necesitamos consultar competidores sin ninguna cuenta de vendedor, Keepa es la opción práctica de las tres estudiadas.** No hemos contratado servicios.

El estimador sigue siendo nuestro. Ninguna de estas conexiones entrega un registro completo de ventas e ingresos reales de cualquier competidor. Cambia la obtención de sus señales, no la fórmula ni la definición de ventas reales.

- **SP-API:** oficial, catálogo de ASIN ajenos y ofertas según roles, acceso concedido y cobertura. No devuelve las ventas privadas de esos competidores ni recupera históricos de ranking/precio. Las tarifas de desarrollador anunciadas para 2026 fueron canceladas: Amazon informa que no aplica por ahora cuotas anuales ni por uso de SP-API. Esto no elimina costes propios de alojamiento ni de cuentas de vendedor. [Anuncio oficial](https://developer.amazonservices.com/cancellation-of-sp-api-fees).
- **Keepa:** independiente de Amazon. Documenta Amazon México (`domain=11`), precios y rankings históricos de productos competidores. Plan Starter mostrado en su página oficial: **49 EUR/mes y 20 tokens/minuto**, consultado el 28.10.2026. No requiere cuenta de vendedor. La disponibilidad efectiva del histórico de cada uno de nuestros seis ASIN sigue pendiente de una consulta autenticada. [Planes](https://keepa.com/api/pricing), [consulta de productos y dominios](https://keepa.com/api-docs/product.html).
- **Creators API:** oficial, orientada a afiliados y compras, con catálogo, variantes y ofertas actuales; no anuncia históricos de BSR/precio. Su finalidad y requisitos la hacen peor base para Nexo. Requiere Amazon Associates en el mercado objetivo, registro y el umbral publicado de 10 ventas calificadas en los últimos 30 días. La documentación consultada no publica una tarifa por llamada; aplica límites y requisitos comerciales. [Introducción y requisitos](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/introduction), [límites](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/concepts/api-rates), [uso previsto](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/concepts/best-programming-practices).

## Cobertura de campos

«Sí» significa que existe el recurso o campo, no que todos los ASIN siempre lo devuelvan.

| Campo | Amazon SP-API | Amazon Creators API | Keepa |
|---|---|---|---|
| ASIN consultado / padre / hijos | ASIN y relaciones VARIATION, cuando existan | ASIN, ParentASIN y GetVariations paginado | ASIN, parentAsin y variaciones; la lista puede ser de hermanos, no solo hijos |
| Marketplace / categoría | marketplaceId, clasificaciones y nombres | marketplace y BrowseNodeInfo | domainId=11 y categoryTree |
| BSR actual | SalesRanks por clasificación/grupo | Rankings de BrowseNodeInfo, según producto/recurso | SalesRankReference, salesRanks y estadísticas |
| BSR histórico anterior a nuestra conexión | No; guardar observaciones desde ahora | No documentado | Sí, historial por categoría si el producto fue seguido |
| Precio actual | Product Pricing, ofertas/Buy Box/mínimos según respuesta | OffersV2 | Series y stats; distinguir Amazon, mínimo nuevo y Buy Box |
| Precio histórico anterior a nuestra conexión | No | No documentado | Sí, según seguimiento y tipo de precio |
| Disponibilidad | Señales de ofertas y envío; no inventario universal | Disponibilidad de ofertas devueltas | Señales de precio/ofertas/stock; cobertura parcial y opciones con coste |
| Variantes | Relaciones y atributos | GetVariations | Lista/historial; ciertos refrescos/opciones requieren tokens adicionales |
| Número de vendedores | Contadores de ofertas; GetItemOffers devuelve hasta 20 ofertas. Vendedores únicos devueltos son un subconjunto | Comerciantes de las ofertas devueltas; no censo garantizado | COUNT_NEW y ofertas opcionales; declarar el alcance del recuento |
| Señales para estimar | Ranking, categoría, precio, relaciones, competencia; snapshots propios | Catálogo y ofertas actuales | Históricos, cambios de precio/ranking, competencia, umbrales públicos de compras cuando existan |
| Ventas e ingresos reales de competidores | No | No | No; monthlySold representa el umbral público de compras, no unidades exactas |
| Fecha/hora de consulta | La registra Nexo; no confundir con actualización del origen | Igual | Nexo registra consulta y conserva lastUpdate/lastOffersUpdate/lastStockUpdate por separado |

Fuentes de campos: [GetCatalogItem](https://developer-docs.amazon/sp-api/reference/getcatalogitem), [GetItemOffers](https://developer-docs.amazon/sp-api/reference/getitemoffers), [Creators GetItems](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/api-reference/operations/get-items), [Creators variantes](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/api-reference/operations/get-variations), [Creators ofertas](https://affiliate-program.amazon.com/creatorsapi/docs/en-us/api-reference/resources/offersV2), [Keepa objeto Product](https://keepa.com/api-docs/product-object.html).

## Acceso y configuración segura

### Opción oficial: SP-API

No necesitamos vender nosotros para registrarnos como desarrollador público, pero sí completar el alta y aprobación correspondientes y obtener autorización de un vendedor para las operaciones elegidas. Una clave cualquiera del profesor no sustituye ese proceso. La vía de aplicación privada depende de la organización propietaria y no debe confundirse con distribuir Nexo a terceros.

1. Registrar el desarrollador y la aplicación Nexo en [Solution Provider Portal](https://solutionproviderportal.amazon.com/) siguiendo el [alta de desarrollador público](https://developer-docs.amazon/sp-api/docs/register-as-a-public-developer).
2. Solicitar los roles exigidos para Catalog Items y Product Pricing: Product Listing y Pricing, según operaciones/aprobación. La aplicación implementada solo consulta catálogo y ofertas; no modifica listings, precios ni pedidos.
3. Configurar el flujo OAuth de la aplicación y hacer que el profesor/vendedor la autorice desde Amazon. Este primer intercambio requiere un flujo de autorización aprobado; **no está implementada una pantalla pública de alta de vendedores en el piloto**. No pedir su contraseña.
4. Obtener el Client ID y Client Secret de Login with Amazon y el refresh token del vendedor autorizado. El código sí intercambia ese refresh token por un access token temporal y lo renueva en memoria.
5. Guardarlos mediante `python3 -m nexo_data configure sp-api` desde la carpeta `api/`. Se solicitan ocultos. Alternativamente, configurar secretos del servidor con los nombres de `.env.example`; el archivo de ejemplo no se carga automáticamente.

México usa `A1AM78C64UM0Y8` y la región NA. Aprobación, acceso efectivo a ASIN de competidores y permisos de uso comercial deben validarse con nuestra aplicación concreta; no se han dado por concedidos. [Onboarding](https://developer-docs.amazon.com/sp-api/docs/onboarding-overview).

### Opción inmediata sin vendedor: Keepa

1. Crear o usar una cuenta Keepa y, si se aprueba el gasto, contratar el plan de **API**; no confundirlo con una suscripción de interfaz web. No hemos comprado nada.
2. Obtener la clave en el área API de esa cuenta.
3. En este equipo, ejecutar `python3 -m nexo_data configure keepa` desde `api/` e introducirla en la entrada oculta. No mandarla por chat, ponerla en JavaScript ni subirla al repositorio.
4. Ejecutar la primera sincronización de los seis ASIN. Comprobar cobertura, consumo, antigüedad y campos antes de ampliar el catálogo.

La consulta básica cuesta **1 token por producto**; solicitar `history`, `days` o `stats` no añade coste por sí mismo. Seis ASIN sin extras consumen normalmente seis tokens por ronda. `offers` cambia el cálculo: 6 tokens por página de ofertas encontrada; no es simplemente 1+6. Stock, Buy Box y ciertas opciones de variantes/reviews tienen reglas adicionales. La configuración inicial evita esos extras. [Tokens y planes](https://keepa.com/api-docs/plans-tokens.html), [parámetros](https://keepa.com/api-docs/product.html).

Un plan de acceso no equivale automáticamente a permiso de redistribuir respuestas crudas o revender un espejo de Keepa. Antes de abrir el servicio a clientes hay que confirmar el uso comercial concreto. Se mantiene la separación entre señales del proveedor y resultados del estimador propio.

## Lo implementado y lo realmente probado

- Dos clientes de consulta: Keepa y SP-API; sin usar navegador para adquirir datos de Amazon.
- Consulta por ASIN de nuestros seis productos, lotes de hasta 100 en Keepa; fecha, procedencia y ausencia de campos explícitas.
- Almacenamiento SQLite de snapshots e históricos normalizados, deduplicación, estado de sincronizaciones y API local de lectura.
- Sincronización periódica opcional. Los visitantes leen la base de datos y no disparan peticiones pagadas al proveedor.
- Interfaz anterior conservada, con carga opcional desde nuestro servidor y gráfico de precios solo cuando hay histórico recibido. GitHub Pages conserva la muestra consultada previamente mientras no exista un servidor conectado.
- Secretos locales separados, permisos de archivo restringidos y exclusión de Git. Las URLs/errores con claves no se imprimen.
- **15 pruebas unitarias superadas con respuestas sintéticas**, más comprobación HTTP local. Eso verifica tratamiento de datos y funcionamiento del código, no precisión comercial ni autenticación externa.

**Intento real:** ambos servidores externos son alcanzables. Keepa respondió HTTP 400 sin clave; SP-API, HTTP 403 sin autorización. **Cero productos recibidos por API; ninguna conexión autenticada validada.** No hay credenciales configuradas. El resultado está en `api/diagnostico-api.json`. Podemos realizar llamadas HTTPS desde este entorno; las credenciales y aprobaciones son el bloqueo actual.

## Cómo aprovecha el modelo los históricos

Se conserva el estimador existente y su requisito de referencias reales. Keepa entrega series de cambios, no necesariamente un punto cada día. El nuevo módulo calcula ranking geométrico y precio medio ponderados por tiempo, por categoría y ventana de 30 días. Detecta huecos, sentinelas negativos y cambios de categoría; no convierte ausencia de dato en cero ventas.

Se limita el arrastre de una observación a 24 horas por defecto y se exige 90 % de cobertura para declarar una ventana utilizable. Son filtros conservadores del piloto, no evidencia de exactitud del proveedor: pueden descartar series de eventos escasas y deberán revisarse con datos reales. **No se entrena automáticamente**: faltan unidades reales del mismo ASIN, mercado, categoría y periodo. El BSR actual aislado no se presenta como promedio mensual.

Las ventas de una cuenta del profesor son sus ventas, no necesariamente todas las del ASIN si hay otros vendedores. monthlySold/contadores públicos y estimaciones Helium/Jungle son referencias auxiliares, no verdad de entrenamiento. No se puede prometer un 80 %, 90 % o 95 % de precisión por cambiar a API.

## Despliegue y siguiente paso

GitHub Pages aloja archivos estáticos; no guarda secretos ni ejecuta estas consultas. El piloto se ejecuta en el ordenador con Python y SQLite. Para servir datos actualizados públicamente, el siguiente despliegue será un servicio en nube con HTTPS, secretos, tarea programada y almacenamiento persistente. El ordenador no necesita estar encendido cuando el servicio viva en nube.

Se conserva una arquitectura ampliable, pero **el servidor incluido es de desarrollo local**, enlazado a 127.0.0.1. Antes de producción faltan servidor de aplicación y proxy adecuados, acceso de usuarios, cuotas, cola con presupuesto de tokens, supervisión, copias de seguridad y validación de licencias. No hace falta comprar un Mac mini para este piloto.

Acción que desbloquea la comprobación real: autorización SP-API de un vendedor con aplicación aprobada, o clave de un plan Keepa API activo. Recomendación económica: avanzar primero el alta oficial con el profesor y mantener Keepa preparado sin contratarlo todavía. Si se necesita histórico previo inmediatamente, Keepa es la vía concreta a evaluar.
