# Alta oficial de Nexo en Amazon

Estado del 29.10.2026: Gonzalo elige SP-API y dispone de cuenta de comprador. El profesor ofrece Excel de ventas y acceso Helium 10; aún no entregados. No hay autorización SP-API, aplicación registrada ni cuenta desarrolladora confirmadas.

## Paso inmediato

Entrar con la cuenta Amazon en https://solutionproviderportal.amazon.com/ . Se ha abierto el portal y muestra «Iniciar sesión»; el usuario debe completar su acceso. No hace falta abrir una tienda propia para la vía de desarrollador público. La aprobación no está garantizada.

La [documentación oficial de alta pública](https://developer-docs.amazon/sp-api/docs/register-as-a-public-developer) exige perfil, web de servicios accesible y roles, con revisión. Posteriormente cada vendedor autoriza mediante OAuth. Las aplicaciones públicas deben cumplir las condiciones del Selling Partner Appstore. No se ha enviado ninguna solicitud ni aceptado acuerdos en nombre de Gonzalo.

## Información ya preparada

- Nombre del proyecto: Nexo Commerce.
- Sitio: https://gonzalosystems.github.io/nexo-commerce-demo/ . Es una demo, no se presenta como servicio con clientes o conexión activa.
- Mercado inicial: Amazon México.
- Función prevista: investigación de productos para vendedores; consulta por ASIN/palabras clave/categoría/marca, seguimiento de rankings y ofertas y cálculo propio de unidades a partir de referencias comparables.
- Operaciones implementadas: Catalog Items v2022-04-01 `getCatalogItem` y `searchCatalogItems`; Product Pricing v0 `getItemOffers`. Solo lectura de catálogo/ofertas. LWA usa POST para renovar tokens; no modifica publicaciones, precios ni pedidos.
- Pedir únicamente los roles que corresponden a esas operaciones (Product Listing y Pricing según mapeo vigente). No solicitar datos personales de compradores ni roles restringidos que el producto no necesita.

## Información pendiente del titular

El formulario puede pedir nombre legal/tipo de actividad, dirección/contacto y descripción de controles. Esos datos no se inventan. Tampoco se afirma que exista infraestructura de producción que aún no está desplegada.

Estado técnico real: claves locales fuera de Git, entrada oculta, archivo con permisos 600; servidor de prueba solo localhost y base SQLite. Para producción faltan despliegue HTTPS del backend, gestión de secretos apropiada, acceso, copias/supervisión y flujo OAuth público con callback registrado. No declarar completados esos controles en la solicitud.

El flujo inicial de OAuth y la web de autorización del vendedor se implementarán con la configuración real de la aplicación. El cliente actual ya sabe renovar un refresh token válido; no genera autorizaciones por sí mismo.

## Búsqueda implementada mientras esperamos

La CLI del backend incorpora `search`, probada con respuestas sintéticas y bloqueada correctamente sin credenciales:

```sh
python3 -m nexo_data search --keywords audifonos --brand Sony
python3 -m nexo_data search --asins B0CFSCT8GQ B0C1HGKNG7
```

Con palabras clave acepta `--classification-id ID_NUMERICO` y `--page-token TOKEN` para la siguiente página, hasta 20 resultados por llamada. La categoría se envía como identificador de Amazon, no como una etiqueta inventada. No se mezclan ASIN con palabras clave/marca/categoría en la misma petición. `--save` almacena las fichas recibidas; no activa búsquedas públicas ni incorpora automáticamente nuevos productos a la demo de seis fichas.

SP-API no ofrece filtros de ventas estimadas ni convierte nuestra aplicación en una base de datos completa como Black Box. Precio/BSR/reseñas se filtran sobre los datos que ya tengamos guardados; la búsqueda oficial incorpora los filtros admitidos por Amazon. [Referencia de búsqueda](https://developer-docs.amazon/sp-api/reference/searchcatalogitems).

## Referencia de interfaz

La estructura de producto/competencia/ventas y búsqueda simple/avanzada se ha contrastado con [Black Box: Products Tab](https://kb.helium10.com/hc/en-us/articles/6710274045339-Black-Box-Product-Tab-Overview) y su [guía de filtros](https://kb.helium10.com/hc/en-us/articles/360034015153-Tutorial-Navigating-the-Black-Box-Dashboard). Implementación propia con identidad Nexo, sin acceso a la sesión privada Helium ni reutilización de su código.

La demo filtra seis productos reales del catálogo guardado por categoría, marca, tipo, ASIN/lista, precios, opiniones, valoración y BSR. Ventas/ingresos calculados se habilitan solo con cálculos disponibles; vendedores, solo con el campo recibido por API. Mercado Libre tiene identificadores y ámbito propios; no recibe el BSR de Amazon.
