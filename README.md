# Dexora Cards

Plataforma web y móvil para explorar las especies de la Pokédex nacional, consultar sus cartas físicas de Pokémon TCG y registrar colecciones personales bajo la identidad **Dexora Cards**.

> Proyecto comunitario no oficial. No está afiliado, respaldado ni patrocinado por Nintendo, Creatures Inc., Game Freak ni The Pokémon Company. Las marcas e imágenes pertenecen a sus respectivos titulares.

## Arquitectura

- `config/`: configuración Django, URLs raíz y despliegue WSGI/ASGI.
- `core/`: inicio, estadísticas cacheadas y contenido común.
- `catalog/`: especies, expansiones, cartas, consultas, integración con APIs, admin y comandos.
- `collections_app/`: inventario personal, cantidades, variantes y condiciones, con eliminación individual o masiva mediante confirmación segura. Su etiqueta Django es `collections` sin colisionar con el módulo estándar de Python.
- `pokedex_app/`: progreso personal de especies obtenidas para **Mis 1025 Pokémon**, separado de las cartas TCG.
- `wishlist_app/`: lista privada de cartas deseadas, filtros y acciones rápidas mediante estrellas SVG.
- `api/`: API JSON autenticada por token para los clientes móviles.
- `users/`: registro, perfil de coleccionista personalizable y formularios de cuenta; autenticación y recuperación usan Django Auth.
- `mobile/`: aplicación Flutter para Android/iOS con Cardex, Pokédex personal, colección, wishlist y perfil.
- `templates/`: vistas semánticas y parciales HTMX.
- `static/`: CSS, JavaScript modular y placeholder local.

Las páginas públicas solo leen la base local. Las URLs de imágenes oficiales se conservan remotas; únicamente las sustituciones administrativas se guardan en `media/`. Las especies usan ilustraciones oficiales de PokéAPI con prioridad `custom_artwork`, URL remota y placeholder. Las cartas usan `custom_image`, imagen grande remota, imagen pequeña remota y placeholder. El Cardex mantiene una sola entrada por especie nacional, pero reúne bajo ella todas las cartas de formas regionales y variantes; la ficha muestra los tipos y nombres/formas TCG presentes para hacer visible esa cobertura.

Cada usuario puede personalizar su perfil con avatar, portada horizontal, nombre visible, título de coleccionista, lema, biografía, ubicación opcional, antigüedad, Pokémon y tipo favoritos, color de acento y una carta destacada. Por privacidad, el correo no se muestra públicamente y la carta destacada solo puede seleccionarse entre las cartas de la colección del propio usuario.

## Requisitos

- Python 3.12+
- PostgreSQL 15+ recomendado; SQLite funciona para desarrollo y demo
- Docker Compose opcional
- Flutter 3.38+ y Android Studio/Xcode para compilar la aplicación móvil

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

## Aplicación móvil

La app Flutter reutiliza los usuarios y el catálogo del backend. El token de sesión se guarda mediante el almacén seguro del sistema operativo. **Mis 1025 Pokémon** es una colección general de especies: marcar un Pokémon como obtenido no añade cartas TCG y añadir una carta no marca automáticamente la especie.

El módulo presenta 16 especies por página en una cuadrícula 4×4, búsqueda, filtros por estado, progreso total y registro directo de obtenido/pendiente. La API fija el tamaño de página en 16 para que el comportamiento sea consistente en todos los dispositivos.

Inicia primero el backend para un emulador Android:

```powershell
python manage.py migrate
python manage.py runserver 0.0.0.0:8002
```

Después ejecuta Flutter:

```powershell
cd mobile
flutter pub get
flutter run --dart-define=DEXORA_API_URL=http://10.0.2.2:8002/api/v1
```

`10.0.2.2` representa el equipo anfitrión desde el emulador Android. Para un dispositivo físico usa la IP LAN del equipo, añade esa IP a `DJANGO_ALLOWED_HOSTS` y conserva ambos dispositivos en la misma red. Para iOS Simulator puede usarse `http://127.0.0.1:8002/api/v1`. Producción debe usar HTTPS y desactivar tráfico HTTP plano.

Comprobaciones móviles:

```powershell
cd mobile
dart format --output=none --set-exit-if-changed lib test
flutter analyze
flutter test
flutter build apk --debug
```

### API móvil

La API vive bajo `/api/v1/`. Sus recursos principales son `auth/login`, `dashboard`, `species`, `cards`, `collection`, `wishlist`, `my-pokemon` y `profile`. Salvo el inicio de sesión, todos exigen `Authorization: Token …`. Las consultas privadas siempre se limitan al usuario autenticado.

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

Las pruebas usan SQLite temporal y mocks, nunca las APIs reales. Cubren modelos, restricciones, prioridad de imagen, relaciones, búsqueda/filtros, comandos, permisos, ciclo de colección y wishlist, formularios de imagen, registro, páginas principales y API móvil. Flutter incluye pruebas de modelos y componentes, además de análisis estático.

El repositorio incluye GitHub Actions en `.github/workflows/ci.yml`. Cada push o pull request contra `main` valida las migraciones, ejecuta los checks, las pruebas con PostgreSQL 17, la compilación de archivos estáticos, el análisis y las pruebas Flutter y un APK Android de depuración. Las credenciales del workflow son efímeras y exclusivas del contenedor de CI.

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
- La aplicación móvil usa Flutter y una API DRF con tokens revocables, límites de solicitudes y aislamiento de datos por usuario.

## Limitaciones conocidas del MVP

- El progreso muestra especies cubiertas y totales globales; porcentajes exhaustivos por expansión requieren decidir qué variantes cuentan como objetivo.
- La recuperación de contraseña está preparada, pero necesita un proveedor SMTP para enviar correo real.
- Las imágenes remotas dependen de la disponibilidad y políticas de la API de origen.
- SQLite no reproduce todas las características de concurrencia de PostgreSQL.
- No incluye venta, precios, intercambios, mensajería, sobres virtuales ni pagos.
- El MVP móvil aún no ofrece modo sin conexión ni notificaciones; requiere conectividad con el backend.
