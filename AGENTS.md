# AGENTS.md

## Mapa del repositorio

- `config`: settings y enrutamiento raíz.
- `core`: inicio y elementos globales.
- `catalog`: modelos TCG/Pokédex, selectores, servicios API, comandos y admin.
- `collections_app`: colección privada del usuario (app label `collections`).
- `pokedex_app`: especies obtenidas en la colección Pokémon general.
- `wishlist_app`: cartas deseadas y acciones rápidas privadas.
- `api`: API REST autenticada para clientes móviles.
- `mobile`: aplicación Flutter Android/iOS.
- `users`: registro; Django Auth resuelve sesiones y contraseñas.
- `templates`, `static`, `media`: presentación y subidas locales.

## Convenciones

- Python 3.12+, Django 5.2; vistas delgadas y consultas complejas en `selectors.py`.
- Integraciones externas en `services.py`; páginas públicas nunca consultan APIs.
- Plantillas en español, HTML semántico y estilos reutilizables en `static/css/app.css`.
- Usar `select_related`/`prefetch_related`, paginación e índices para catálogos.
- Migraciones versionadas para todo cambio de modelo.
- La Pokédex personal pagina siempre 16 especies para conservar la cuadrícula móvil 4×4.
- Flutter usa `--dart-define=DEXORA_API_URL=...`; nunca escribir hosts de producción ni tokens en el código.

## Comandos

```text
python manage.py runserver
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
python manage.py seed_demo
cd mobile && flutter analyze
cd mobile && flutter test
```

## Definición de terminado

Una tarea debe incluir migraciones si aplican, pruebas relevantes, `check` limpio, revisión responsive/teclado, documentación actualizada y diff sin código accidental ni secretos.

## Protección de datos

- Nunca versionar `.env`, claves de API, contraseñas, base local ni `media/`.
- No descargar en masa imágenes remotas. Guardar URLs y usar `custom_image` solo para sustituciones autorizadas.
- Una sincronización nunca debe sobrescribir `custom_image`, `image_source`, `is_visible` ni decisiones editoriales locales expresamente protegidas.
- Toda operación de colección debe filtrar por `request.user`; administración y carga manual requieren personal autorizado.
