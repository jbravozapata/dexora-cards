# Dexora Cards

MVP web para explorar las especies de la Pokédex nacional, consultar sus cartas físicas de Pokémon TCG y registrar una colección personal bajo la identidad **Dexora Cards**.

> Proyecto comunitario no oficial. No está afiliado, respaldado ni patrocinado por Nintendo, Creatures Inc., Game Freak ni The Pokémon Company. Las marcas e imágenes pertenecen a sus respectivos titulares.

## Arquitectura

- `config/`: configuración Django, URLs raíz y despliegue WSGI/ASGI.
- `core/`: inicio, estadísticas cacheadas y contenido común.
- `catalog/`: especies, expansiones, cartas, consultas, integración con APIs, admin y comandos.
- `collections_app/`: inventario personal, cantidades, variantes y condiciones. Su etiqueta Django es `collections` sin colisionar con el módulo estándar de Python.
- `wishlist_app/`: lista privada de cartas deseadas, filtros y acciones rápidas mediante estrellas SVG.
- `users/`: registro, perfil de coleccionista personalizable y formularios de cuenta; autenticación y recuperación usan Django Auth.
- `templates/`: vistas semánticas y parciales HTMX.
- `static/`: CSS, JavaScript modular y placeholder local.

Las páginas públicas solo leen la base local. Las URLs de imágenes oficiales se conservan remotas; únicamente las sustituciones administrativas se guardan en `media/`. Las especies usan ilustraciones oficiales de PokéAPI con prioridad `custom_artwork`, URL remota y placeholder. Las cartas usan `custom_image`, imagen grande remota, imagen pequeña remota y placeholder. El Cardex mantiene una sola entrada por especie nacional, pero reúne bajo ella todas las cartas de formas regionales y variantes; la ficha muestra los tipos y nombres/formas TCG presentes para hacer visible esa cobertura.

Cada usuario puede personalizar su perfil con avatar, portada horizontal, nombre visible, título de coleccionista, lema, biografía, ubicación opcional, antigüedad, Pokémon y tipo favoritos, color de acento y una carta destacada. Por privacidad, el correo no se muestra públicamente y la carta destacada solo puede seleccionarse entre las cartas de la colección del propio usuario.

## Requisitos

- Python 3.12+
- PostgreSQL 15+ recomendado; SQLite funciona para desarrollo y demo
- Docker Compose opcional

## Instalación local

En PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

Abre `http://127.0.0.1:8000/`. `seed_demo` es idempotente y añade 10 especies y 10 cartas abstractas sin imágenes oficiales, suficientes para revisar todas las vistas sin acceso a las APIs.

En macOS/Linux cambia la activación por `source .venv/bin/activate` y usa `cp .env.example .env`.

## Variables de entorno

Copia `.env.example` a `.env`. El archivo real está ignorado por Git.

| Variable | Uso |
| --- | --- |
| `DJANGO_SECRET_KEY` | Secreto único; obligatorio cambiarlo en producción |
| `DJANGO_DEBUG` | `True` solo en desarrollo |
| `DJANGO_ALLOWED_HOSTS` | Hosts separados por comas |
| `DATABASE_URL` | `sqlite:///db.sqlite3` o URL PostgreSQL |
| `POKEMON_TCG_API_KEY` | Clave del servidor para Pokémon TCG API; nunca llega al navegador |
| `DJANGO_SECURE_SSL_REDIRECT` | Activa redirección HTTPS en producción |
| `EMAIL_BACKEND` | Backend de correo; por defecto imprime recuperación en consola |

Ejemplo PostgreSQL local:

```env
DATABASE_URL=postgresql://dexecuador:una-clave-segura@localhost:5432/dexecuador
```

Crea la base y usuario con las herramientas de PostgreSQL, actualiza `.env` y ejecuta `python manage.py migrate`.

## Sincronización

Ejecuta en este orden:

```powershell
python manage.py sync_pokemon_species
python manage.py sync_tcg_sets
python manage.py sync_tcg_cards
python manage.py link_unlinked_tcg_cards
```

`link_unlinked_tcg_cards` repara cartas Pok&eacute;mon cuyo proveedor omiti&oacute; `nationalPokedexNumbers`, usando una coincidencia segura con el nombre ingl&eacute;s de Pok&eacute;API. Las relaciones administrativas existentes se conservan.

Opciones útiles durante desarrollo:

```powershell
python manage.py sync_pokemon_species --limit 25
python manage.py sync_pokemon_species --missing-only
python manage.py sync_tcg_cards --page-size 100 --max-pages 2
python manage.py sync_tcg_cards --page-size 250 --start-page 2
```

Los clientes aplican timeout, reintentos con espera incremental y validación básica. Cada comando usa claves externas únicas con `update_or_create`, procesa páginas/lotes y puede repetirse. La sincronización de especies conserva `custom_artwork`; `--missing-only` completa las ilustraciones ausentes. La sincronización de cartas conserva `custom_image`, `image_source`, `is_visible` y el `slug` local; actualiza los metadatos externos y reconstruye la relación de especies desde `nationalPokedexNumbers`. Los fallos por registro se escriben en el log y no detienen el lote completo.

## Administración

Accede a `/admin/` con un superusuario. Se pueden buscar y filtrar especies, expansiones, cartas, colecciones y wishlists; editar relaciones muchos-a-muchos; controlar visibilidad; previsualizar imágenes; y cargar ilustraciones personalizadas de especies o cartas en JPG, PNG o WebP de hasta 8 MB. También existe un formulario administrativo enlazado desde el detalle de cada carta.

## Pruebas y comprobaciones

```powershell
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
python manage.py collectstatic --noinput
```

Las pruebas usan SQLite temporal y mocks, nunca las APIs reales. Cubren modelos, restricciones, prioridad de imagen, relaciones, búsqueda/filtros, comandos, permisos, ciclo de colección y wishlist, formularios de imagen, registro y páginas principales.

El repositorio incluye GitHub Actions en `.github/workflows/ci.yml`. Cada push o pull request contra `main` valida las migraciones, ejecuta los checks, las pruebas con PostgreSQL 17 y la compilación de archivos estáticos. Las credenciales del workflow son efímeras y exclusivas del contenedor de CI.

## Docker y PostgreSQL

```powershell
Copy-Item .env.example .env
docker compose up --build
docker compose exec web python manage.py seed_demo
docker compose exec web python manage.py createsuperuser
```

La aplicación queda en `http://localhost:8000/`. PostgreSQL y `media/` usan volúmenes persistentes. Para producción deben configurarse secretos reales, HTTPS, correo transaccional, almacenamiento persistente de medios y un proxy/CDN.

## Decisiones técnicas

- Django 5.2 LTS, Templates y HTMX; sin framework frontend pesado.
- PostgreSQL principal con SQLite como salida local inmediata.
- Índices en número nacional, nombre, generación, tipos, visibilidad y rareza.
- `select_related`, `prefetch_related`, agregaciones y paginación de servidor en las vistas de mayor tráfico.
- Estadísticas de inicio cacheadas cinco minutos.
- Imágenes con dimensiones explícitas, `loading="lazy"` y sustituciones locales protegidas.
- Seguridad preparada mediante CSRF, autorización por propietario, validación de imágenes, cookies seguras/HSTS fuera de debug y secretos por entorno.

## Limitaciones conocidas del MVP

- El progreso muestra especies cubiertas y totales globales; porcentajes exhaustivos por expansión requieren decidir qué variantes cuentan como objetivo.
- La recuperación de contraseña está preparada, pero necesita un proveedor SMTP para enviar correo real.
- Las imágenes remotas dependen de la disponibilidad y políticas de la API de origen.
- SQLite no reproduce todas las características de concurrencia de PostgreSQL.
- No incluye venta, precios, intercambios, mensajería, sobres virtuales ni pagos.
