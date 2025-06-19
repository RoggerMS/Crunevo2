# Guidelines for Codex agents

- Always run `make fmt` and `make test` before committing.
- Use Tailwind CSS utilities when updating templates, but keep Bootstrap components unless instructed otherwise.
- Do not modify models or database migrations unless explicitly requested.
- The notes blueprint exposes both `notes.detail` and `notes.view_note` for `/notes/<id>`.
- Merge duplicated `DOMContentLoaded` listeners into a single entry point in `main.js`.
- All `<form method="post">` must import `components/csrf.html` and call
  `csrf_field()` immediately after the `<form>` tag.
- Nunca hacer CREATE TYPE sin comprobar si el tipo ya existe; usa IF NOT EXISTS o checkfirst=True.
- Se corrigió la barra de navegación fija añadiendo padding global y mejorando el menú móvil (PR navbar fixes).
- Se ajustó el padding global mediante CSS en el body y se agregó z-index al navbar para evitar que tape el contenido.
- Se mejoró el cierre del menú móvil y se fijó la altura del navbar (PR navbar fixes 2).
- Se cierra el menú móvil al redimensionar la pantalla (PR navbar fixes 3).
- Se movió el padding-top global al archivo style.css y se eliminó el bloque de
  estilos embebidos en base.html (PR navbar fixes 4).
- Se ajustó el `main` con padding-top en móviles y se quitó en pantallas
  mayores (PR navbar fixes 5).
- Se agregó margen superior al `main` solo en escritorio con CSS
  (`@media (min-width: 992px)`)
- Se oculta `#mobileMenuOverlay` en escritorio y se ajusta el
  listener de redimensionado a 992px (PR overlay fix).
- Se establece `height` y `width` en 0 para `#mobileMenuOverlay` en
  escritorio y se asegura que `closeMenu()` añada `tw-hidden` (PR overlay fix 2).
- Se corrige la clase inicial de `#navLinks` para mostrarse horizontal en
  escritorio y se evita abrir el menú móvil en pantallas grandes
  (PR navbar desktop fix).
- Se establece `z-index: -1` y `position: static` para `#mobileMenuOverlay`
  en escritorio, previniendo que bloquee el contenido (PR overlay fix 3).
- Se asegura que `#navLinks` se coloque en `#desktopNavContainer` al cargar la
  página y se oculta `#mobileMenuPanel` en escritorio (PR navbar panel fix).
- Se fuerzan `display: none` y `pointer-events: none` para `#mobileMenuOverlay`
  y `#mobileMenuPanel` en escritorio, actualizando `main.js` para aplicar estos
  estilos al cargar la página y al cerrar el menú (PR overlay hide complete).

- Se agregó "navbar_crunevo_fixed.html" como ejemplo de navbar fijo con menú móvil.
- Navbar migrado completamente a Bootstrap sin Tailwind ni overlay. Se eliminó el script de Tailwind y se simplificó main.js (PR bootstrap-only navbar).
- Implemented Tabler-based admin dashboard with new templates and blueprint enforcement.
- Fixed PDF upload to Cloudinary storing URL and adjusted templates (PR pdf-upload-fix).
- Restored Cloudinary upload logic in `notes_routes.py` to fix undefined variable error (PR notes-upload-fix).
- Improved PDF handling in notes: use `resource_type='auto'`, display inline with `<iframe>` and direct download link (PR notes-pdf-view).
- Enhanced notes upload error handling and download route: validate title, catch Cloudinary errors and serve local files with `send_file` (PR notes-error-handling).
- Updated notes detail template to embed PDFs with an `<iframe>` wrapped in `.ratio`, added fallback download link and removed duplicate buttons (PR pdf-viewer-fix).

- Confirmed notes upload uses `resource_type='auto'` for Cloudinary; recommended verifying URL uses '/raw/upload' (answer to resource_type question).
- Forced Cloudinary URLs for notes to use `resource_type='raw'` when generating
  `secure_url` (PR notes-raw-url).
- Ajustado el flujo de subida de PDF a Cloudinary para almacenar `resource_type='image'` en la URL principal. Esto permite visualizar correctamente el archivo en un `<iframe>` sin bloqueos por `/raw/upload`.
- Reemplazado iframe de detalle de nota para usar Google gview y permitir visualización embebida (PR gview-iframe).
- Se integró PDF.js como visor en `detalle.html`, cargando el primer canvas con el PDF y manteniendo enlace de descarga. (PR pdfjs-viewer)
- Integrado PDF.js de forma local y configurado worker en detalle.html (PR pdfjs-local).
- Corregido el path de `pdf.worker.min.js` en `detalle.html` para que PDF.js renderice correctamente (PR pdfjs-worker-path).
- Mejorado `upload.html` para usar tarjeta Bootstrap con `form-floating` y botón primario (PR notes-upload-ui).
- Corregido include en manage_users.html eliminando 'with user=user' para evitar TemplateSyntaxError (PR manage-users-include-fix).
- Modernizado `upload.html` con tarjeta centrada y botón ancho usando Bootstrap 5 (PR notes-upload-modern-card).
- El CSP ahora permite frames desde Cloudinary (PR cloudinary-frame-src).
- Verificada presencia de PDF.js local y worker (>100KB) y correcta configuración del visor en detalle.html. CSP mantiene Cloudinary en `img-src` y `frame-src` (QA pdfjs-check).
- CSP ampliado: `connect-src` incluye Cloudinary y `script-src`/`style-src` permiten CDN (PR cloudinary-csp-connect).

- Actualizado `<header>` en `admin/partials/topbar.html` con clase `navbar-light` (PR admin-topbar-light).
- Navbar ahora usa clase `navbar-crunevo` y `navbar-expand-md`, con iconos en cada enlace (PR navbar-icons).
- Implementado input rápido en el feed para publicar texto e imagen o PDF, mostrando los últimos posts (PR feed-quick-input).
- Corregido url_for en pending.html para usar 'feed.index' y evitar BuildError (PR pending-home-link)
- Añadida sección de destacados en el feed con notas más vistas, posts populares y usuarios con logros recientes (PR featured-posts)
- Añadido ranking semanal y logros recientes en el feed (PR weekly-ranking)
- Corregidos formularios del panel de administración: `manage_users` acepta
  POST, `user_actions.html` importa `csrf_field` y envía `user_id` (PR admin-fixes)
- Fixed feed template to handle posts without an author (PR orphan-posts-fix).
- Simplified author checks in feed template using a local variable (PR feed-author-var).
- Corregido el query de usuarios destacados para agrupar por usuario y ordenar por el logro más reciente (PR top-users-orderby-fix).

- Agregado endpoint `feed.view_post` con plantilla `post_detail.html` para ver publicaciones individuales (PR post-detail-route).
- Se unificó la ruta alias de `feed.view_post` usando <int:post_id> para evitar BuildError en templates.
- Se añadió prueba unitaria para verificar el alias `/posts/<id>` de `feed.view_post` (PR view-post-alias-test).
- Verificadas rutas del feed y sin reproducir BuildError; alias '/posts/<id>' activo (QA feed-view-post-check).

- Revalidado enlace a `feed.view_post`; no se reproduce BuildError y se mantiene alias `/posts/<id>` (QA feed-view-post-check 2).
- Prueba adicional confirma url_for("feed.view_post") genera /post/<id> (QA feed-view-post-check 3).
- Endpoint `feed.view_post` se define explícitamente en la ruta y se comprueba que la blueprint está registrada (QA feed-view-post-check 4).
- Layout updated to use `container-fluid px-md-5` and sidebars distributed per page with row/col system (PR full-width-layout).
- Se corrigió la sección de destacados en feed.html usando filas y columnas Bootstrap para mostrar tarjetas en tres columnas (PR feed-layout-fix).
- Se ajustó 'feed.html' corrigiendo clases y confirmando las columnas de destacados (PR feed-layout-fix2).
- Ajustado el layout de destacados para distribuir correctamente las tarjetas en tres columnas (PR feed-layout-fix3).
- Verificada CSS global sin conflictos y la fila de destacados usa `row-cols-md-3` para asegurar las tres columnas (PR feed-layout-fix4).
- Ajustado layout de admin para separar navbar fijo y añadir padding al contenido (PR admin-spacing-fix).
- Mejorado `base_admin.html` con padding horizontal en el main y sidebar con enlaces actualizados (PR admin-spacing-fix2).
- Admin layout now uses `page` and `page-wrapper`; sidebar muestra Créditos y Estadísticas (PR admin-page-wrapper).
- Agregado bloque de noticias en el feed principal para mostrar anuncios de CRUNEVO (PR feed-news-section)
- Se añadieron likes y comentarios en las publicaciones del feed (PR feed-comments-likes)
- Panel admin rediseñado con Tabler: tema dinámico, sidebar ampliado y cards con shadow (PR admin-tabler-redesign).
- Sidebar del panel admin reorganizado con secciones y estilos para íconos alineados (PR admin-sidebar-design).
- Sidebar resalta enlace activo, toasts usan Bootstrap y topbar incluye botón de tema (PR admin-sidebar-active).
- Layout de admin en dos columnas con sidebar fijo y topbar dentro de main. Sidebar usa `nav flex-column` (PR admin-sidebar-col-fix).
- Añadido sistema de navegación de secciones por botones en el feed (PR feed-section-buttons).
- Estructura de admin modernizada con Tabler 1.3.x: sidebar fijo, topbar simplificada y soporte de tema oscuro (PR admin-modern-layout).
- Fixed like_post to initialize likes when null (PR post-like-null-fix).
- Navbar principal se oculta en /admin usando un condicional en base.html (PR admin-navbar-hide).
- Implementado filtros rápidos en el feed por query string (PR feed-quick-filters).
- Lista de apuntes ahora permite filtrar por recientes, más vistos y categorías y muestra tags en cada tarjeta (PR notes-filters).
- Apuntes admiten comentarios y reacción con likes que se pueden quitar (PR notes-comments-likes).
- Gestión de usuarios ahora incluye acciones rápidas por fila con dropdown y modal para cambiar rol (PR user-quick-actions).
- Panel de productos en admin incluye edición visual, eliminación segura y acceso directo a vista pública (PR admin-product-actions).

- Panel de administración muestra tarjetas con métricas de usuarios, apuntes, tienda, créditos y ranking (PR admin-dashboard-cards).
- Tienda actualizada con grilla Bootstrap y tarjetas con shadow en store.html y product_card.html (PR store-bootstrap-cards).
- Añadida vista de detalle de producto con ruta '/product/<id>' y enlace desde las tarjetas (PR store-product-detail).
- Carrito rediseñado con tabla responsive y controles de cantidad; nuevas rutas para modificar cantidades (PR cart-update).
- Panel de administración ahora incluye vista detallada de movimientos de créditos con tabla y razón (PR admin-credits-history).
- Panel de administración permite exportar usuarios, créditos y productos a CSV (PR admin-exports).
- En el panel de productos se corrigió el enlace a la vista pública usando `store.product_detail` (PR admin-product-link-fix).
- Eliminada la función `create_tables_once` en app.py para evitar timeouts; las tablas se gestionan con migraciones (PR app-init-fix).
- Added Fly.io troubleshooting steps for Postgres connection errors in README (PR fly-release-troubleshooting).
- Updated Fly.io docs to reference `crunevo-db.internal` (PR fly-db-internal-fix).
- Onboarding tokens now use `secrets.token_urlsafe(32)` and no longer encode the email (PR onboarding-token-length).
- Comment form listener now checks element existence with optional chaining in `detalle.html` (PR comment-form-null-check).
- Removed unused today variable from trending route in feed_routes.py (PR trending-today-remove).
- En `add_product` se castea `price` a float y `stock` a int antes de crear el producto (PR admin-add-product-cast).
- Dashboard incluye gráficas de usuarios, apuntes, créditos y productos usando Chart.js (PR admin-dashboard-charts)
- Corregido _fill_series en products_last_3_months pasando 'rows' (PR admin-stats-bugfix)
- Admin panel moved to subdomain burrito.crunevo.com with dedicated Fly app (PR admin-subdomain).
