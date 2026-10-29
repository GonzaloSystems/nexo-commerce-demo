# Nexo: datos de Amazon por API

Piloto local Python 3.10+ sin dependencias externas. Conserva el sitio y los modelos existentes. Consulta por ASIN, no descarga páginas de Amazon. No contiene credenciales ni respuestas autenticadas de productos.

Consultar la investigación, costes y límites en [decisión de APIs](../decision-apis.md). En el repositorio publicado, el mismo documento está en la raíz.

## Arranque

Desde esta carpeta (`api/` en el paquete local, `backend/` en GitHub):

```sh
python3 -m nexo_data doctor
python3 -m nexo_data configure keepa
# O, una vez obtenida la autorización oficial y sus credenciales:
python3 -m nexo_data configure sp-api
python3 -m nexo_data sync --provider auto --days 180
python3 -m nexo_data serve --port 8787 --sync-seconds 3600
```

Abrir http://127.0.0.1:8787/app.html. El sitio se detecta automáticamente en `../site/` (paquete local) o `../` (GitHub). Puede indicarse explícitamente con `--site RUTA`. Se toma la lista de ASIN del catálogo guardado; también `--asins B0C1HGKNG7 ...`. Sin credenciales no hay solicitudes periódicas al proveedor. `doctor --probe both` solo comprueba alcance HTTPS sin autenticar y no recibe productos.

`configure` usa entrada oculta. Guarda `.private/credentials.json` con permisos 600 en carpeta 700. La carpeta también contiene SQLite y se excluye de Git. `.env.example` documenta nombres admitidos; no es un cargador automático de archivos `.env`. Se admiten variables de entorno y, en nube, secretos del proveedor de alojamiento. Nunca pasar claves como argumentos, incluirlas en frontend ni adjuntarlas a informes.

## Flujo y alcance

Proveedor HTTPS, normalización con procedencia y fechas, almacenamiento, API propia de lectura e interfaz. Las visitas no consultan directamente Keepa/Amazon ni consumen tokens. El servidor sincroniza en segundo plano y el navegador lee la copia almacenada cada cinco minutos. No hay scraping de respaldo.

- `providers.py`: Keepa domain11, SP-API NA y LWA. Solo consultas; Product Pricing opcional. SP-API requiere refresh token ya obtenido mediante OAuth autorizado; no incluye el portal público de autorización inicial.
- `normalize.py`: MXN, epoch Keepa, ausencias, umbrales, categorías, relaciones y alcance de recuentos. Precio mínimo nuevo no equivale necesariamente a Buy Box.
- `storage.py`: SQLite, observaciones e históricos deduplicados; combina señales con procedencia. SP-API actual tiene prioridad de campos y Keepa conserva históricos.
- `history.py`: ventanas de 30 días con medias ponderadas y cobertura. No genera etiquetas de ventas ni entrena con estimaciones ajenas.
- `server.py`: servidor de desarrollo, solo localhost. No exponer directamente a Internet.

GET `/api/health`, `/api/products` y `/api/products/ASIN/history?metric=rank&category=ID&provider=keepa`. Los POST se rechazan. No se sirven archivos privados.

```sh
python3 -m nexo_data features --asin B0C1HGKNG7 --category-id ID --start 2026-09-01 --end 2026-09-30
python3 -m unittest discover -s tests -v
```

El comando `features` necesita datos previamente almacenados de esa categoría. Conservar `training_ready=false` hasta contar con ventas reales comparables. Los filtros temporales conservadores pueden excluir series escasas aunque sean válidas como series de cambios.

## Publicación

GitHub Pages sigue mostrando el catálogo guardado: `runtime-config.js` tiene `apiBaseUrl:null`. El servidor local sirve ese archivo con origen relativo y habilita la lectura desde la API local. No publica datos ni compra nada automáticamente.

Para nube: desplegar un backend con HTTPS y tareas programadas, migrar/persistir la base de datos, configurar secretos del alojamiento y acceso de usuarios; servir preferiblemente frontend/API en el mismo origen. El servidor de desarrollo no sustituye ese despliegue. Antes de un catálogo grande, añadir cola, presupuesto de tokens, reintentos diferidos por cuota, alertas y respaldo. El cliente actual limita los reintentos breves y los lotes a 100 ASIN; no es un rastreador masivo listo para producción.

## Búsqueda oficial (29.10.2026)

```sh
python3 -m nexo_data search --keywords audifonos --brand Sony
python3 -m nexo_data search --asins B0CFSCT8GQ B0C1HGKNG7
```

Con palabras clave: `--classification-id ID_NUMERICO` y `--brand NOMBRE`; paginación con `--page-token TOKEN` y `--page-size 20`. No mezclar identificadores con keywords/marca/categoría. `--save` guarda las fichas recibidas. No solicita ofertas por cada resultado ni inventa precios: se puede sincronizar después la selección. Es una herramienta del operador local, no un endpoint público sin control. No incorpora automáticamente fichas nuevas al catálogo visual de seis productos.

18 pruebas sintéticas de backend superadas; la consulta real sin credenciales se detiene antes de enviar una petición. Los filtros del panel operan sobre los datos disponibles, no sobre todo Amazon. Alta y estado documentados en `alta-amazon.md`.
