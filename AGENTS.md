# Guidelines for Codex agents

## Consolidación de rutas de Perfil
- Se unificaron las rutas `/perfil` (perfil propio) y `/perfil/<username>` (perfil público) en una sola vista inteligente `view_profile`.
- Se redireccionaron las rutas antiguas a la nueva estructura unificada.
- Se actualizaron todas las referencias a `url_for('auth.perfil')` en las plantillas para usar `url_for('auth.view_profile', username=current_user.username)`.
- Se actualizaron los condicionales en las plantillas para detectar si el usuario es el propietario del perfil.
- Se eliminaron rutas redundantes como `/perfil_notas` y se redirigieron a la vista unificada con parámetros de tab.
- Se mantuvieron las funcionalidades existentes como actualización de avatar, banner y sección "about".


- Always run `make fmt` and `make test` before committing.
- Use Tailwind CSS utilities when updating templates, but keep Bootstrap components unless instructed otherwise.
- Do not modify models or database migrations unless explicitly requested.
- The notes blueprint exposes both `notes.detail` and `notes.view_note` for `/notes/<id>`.
- Merge duplicated `DOMContentLoaded` listeners into a single entry point in `main.js`.
- All `<form method="post">` must import `components/csrf.html` and call
  `csrf_field()` immediately after the `<form>` tag.
- Nunca hacer CREATE TYPE sin comprobar si el tipo ya existe; usa IF NOT EXISTS o checkfirst=True.
- Dependabot PRs should only be merged after CI passes (`make test`) and prefer squash merges.
- Se corrigió `Referral` para usar `referrer_id` y `referred_id` en las relaciones y evitar errores de nombre.
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
- Panel de administración aislado por completo en burrito.crunevo.com; /admin no se registra en el dominio principal y navbar público sin enlace Admin (PR admin-isolation).
- Pantalla de login exclusiva para admins en /login, redirige al dashboard y se bloquea /admin en www (PR admin-login-isolation).
- Verificada configuración ADMIN_INSTANCE=1 en fly-admin.toml y wsgi_admin.py; login redirige al dashboard y blueprint admin se registra solo en modo admin (QA admin-config-check).
- Confirmado FLASK_APP usa "crunevo.wsgi_admin:app" y create_app separa blueprints según ADMIN_INSTANCE (QA admin-env-check).
- wsgi_admin.py simplificado para importar create_app desde crunevo.app sin variables extra y se verificó FLASK_APP en fly-admin.toml (QA admin-wsgi-cleanup).

- Dockerfile now reads FLASK_APP to run gunicorn, enabling admin instance to use wsgi_admin (PR admin-gunicorn-env).
- Updated create_app to use `is_admin` flag and ensure admin blueprints load only when ADMIN_INSTANCE=1. wsgi_admin.py now sets this variable explicitly (PR admin-blueprint-filter).
- Updated wsgi.py to import create_app from crunevo.app and set FLASK_APP to 'crunevo.wsgi:app' in fly.toml to ensure Gunicorn loads the app correctly (PR wsgi-app-fix).
- Confirmed admin instance loads wsgi_admin via fly-admin.toml and blueprints register only in that mode (QA admin-deploy-fix).
- wsgi_admin.py ahora establece ADMIN_INSTANCE antes de importar create_app para evitar que el panel admin muestre el feed público (PR wsgi-admin-env-order).
- Health check blueprint registered globally and Fly admin HTTP checks configured. Added console log for instance mode (PR admin-health-check).
- Agregado PUBLIC_BASE_URL en config, context processor e enlace absoluto en manage_store para acceder a la tienda pública desde admin.
- Enlaces de perfil y productos en plantillas admin ahora usan PUBLIC_BASE_URL para apuntar al dominio público (PR admin-absolute-links2).
- Implementados logs de productos, notificaciones internas y rol de moderador con modo lectura en admin (PR admin-logs-moderator).
- Health check no redirige a HTTPS para pasar comprobaciones HTTP (PR health-check-http).
- Fixed inactive dropdowns on admin tables by initializing via main.js and adding tooltips (PR admin-dropdowns-init).
- Mejorado diseño visual del panel admin: contraste, colores y botones en modo claro/oscuro (PR admin-ui-polish).
- Sidebar dark theme polished and dropdowns reinitialized after DataTable events, with theme toggle icon updates (PR admin-dark-dropdown-fix).
- Arreglados dropdowns en tablas con getOrCreateInstance y fondo oscuro uniforme en main y tarjetas (PR admin-dropdown-dark-bg).
- Mejorados badges de rol, icono de tema, padding inferior y estilos de main según tema (PR admin-ui-accessibility-fix).
- Ajustados estilos oscuros de cards y badges, y se forzó fondo oscuro en sidebar para cubrir franjas blancas (PR admin-dark-ui-tweak).
- Dropdown de "Más opciones" ocultando tooltip activo y reinicializado tras DataTables; fondo oscuro global en body y container (PR admin-dropdown-tooltip-fix).
- Contraste de hover en el sidebar oscuro, min-height para page-content y textos muted claros; funciones de dropdowns y datatables movidas a admin_ui.js (PR admin-layout-tweak).
- Reparado dropdown de "Más opciones" en tablas admin, corrigiendo conflictos con DataTables y tooltips (PR admin-dropdown-final-fix).
- Ajustado soporte de modo oscuro en feed, apuntes y tienda (PR dark-theme-fix)
- Ensured dropdown containers use position-relative to properly render menus (QA admin-dropdown-container).
- Prevented duplicate dropdown instances by checking getInstance first (QA admin-dropdown-instance-check).
- Avoided tooltip duplication by verifying getInstance and binding show event once (QA admin-tooltip-instance-fix).
- Implemented ranking with tabs and achievements section (PR ranking-achievements).
- Integrado Resend como proveedor de emails y verificación en registro (PR resend-email-provider).
- Fixed feed weekly ranking query removing nonexistent achievement join (PR achievement-table-fix).
- Fixed profile achievements include syntax and feed loop for recent achievements (PR profile-feed-jinja-fix).
- Updated profile templates to use a.badge_code and redesigned personal profile with activity dashboard (PR profile-redesign).
- Fixed slice syntax in perfil.html loops by assigning sorted lists before slicing to avoid TemplateSyntaxError (PR profile-slice-fix).
- Registro permite subir avatar opcional y username único; perfil muestra @username y acepta nueva foto (PR profile-avatar-upload).
- Avatar por defecto se asigna automáticamente si no se sube imagen en el registro (PR default-avatar).
- Registro renovado con tarjeta responsiva, vista previa de avatar y aviso si falla Resend (PR registro-ui-email-fix).
- Implemented secure admin route to send custom emails with preview and sidebar link (PR admin-email-sender).
- Onboarding finish page redesigned with avatar file/url preview and card layout (PR onboarding-finish-ui).
- Ruta /register no se registra en la instancia admin; el registro sólo está disponible en /onboarding/register del dominio público y el login del admin sigue limitado a roles admin o moderador (PR remove-admin-register).
- Pantalla de login renovada con tarjeta doble y estilos responsive; se añadió login.css (PR login-page-redesign).
- Login page updated with transparent card and centered mobile layout (PR login-transparent-blur).
- Register page redesigned with transparent card and additional fields (PR register-redesign).
- Unified registration under /onboarding/register and removed /register route (PR register-unification).
- Login y registro comparten fondo degradado, tarjetas traslúcidas centradas y soporte de modo oscuro (PR login-register-theme).
- Se corrigió el fondo oscuro en login y registro y se actualizó el logo en login (PR login-register-dark-logo).
- Nuevo correo de confirmación con plantilla HTML y confirm_url externo; asunto actualizado (PR confirm-email-html).
- Mejorado login y registro con tarjeta translúcida, ocultar navbar, alternar contraseña y soporte móvil (PR login-register-ux).
- Optimized login and register pages with smoother theme transitions, rotating welcome phrases and accessible password toggles using 🙊/🙈 icons. Dark mode styling fixed (PR login-register-polish).
- Adjusted dark theme backgrounds to true black, improved password toggle alignment and link contrast, added fading welcome phrase rotation and disabled page scrolling (PR login-register-tweak).
- Added theme toggle button on login and register pages, refined dark mode card translucency, extended welcome phrase interval and improved link contrast (PR login-register-theme-toggle).
- Fixed dark theme backgrounds on login and register: body black, wrappers transparent, cards darker (PR login-register-dark-fix).
- Ensured gradient removed in dark mode on login and register, toggle icon updates with stored preference (PR login-register-gradient-fix).
- Corrigidos estilos de login y registro: fondo negro sólido en modo oscuro, frase estable y tema guardado en localStorage (PR login-register-stability-fix).
- Tienda actualizada: precios en soles, canje con créditos y modelo Purchase; panel admin gestiona precio_creditos y flags (PR store-credits).
- Lista de productos rediseñada con tarjetas responsive y badges; agregado store.css para estilos de tienda (PR store-layout).
- Vista de producto rediseñada con imagen grande, badges y botones (PR store-product-page).
- Corregido enlace a detalle de producto en store.html usando 'store.view_product' para evitar BuildError (PR store-detail-link-fix).
- Vista del carrito modernizada con tabla responsive, totales y botones de acción (PR cart-ui-update).
- Documentada propuesta integral de rediseño de la tienda en docs/store_proposal.md.
- Vista de tienda rediseñada completamente con panel lateral de filtros (categoría, precio, créditos), cuadrícula moderna de productos y layout limpio centrado en e-commerce educativo (PR store-redesign-ux).
- Sidebar de tienda reemplazado por menú exclusivo con enlaces de carrito, compras y filtros rápidos (PR store-sidebar).
- Ficha de producto modernizada con sección de características y stock (PR store-product-detail-redesign).
- Sistema de favoritos funcional con modelo FavoriteProduct, rutas y iconos de corazón (PR store-favorites).
- Filtros por categoría y precio habilitados en la tienda (PR store-filters).
- Historial de compras accesible en /store/compras con tarjetas de detalle y opción de descarga (PR store-purchases-page).
- Checkout real crea registros en Purchase y descuenta stock; botón "Comprar ahora" en productos (PR real-checkout).
- Corregido enlace de eliminar del carrito para usar store.remove_item y evitar BuildError (PR fix-cart-remove-link).
- Agregados alias price_paid y credits_used en Purchase, página de éxito para checkout y botones de tienda deshabilitados si no hay stock o créditos insuficientes (PR checkout-success-ui).
- Canje con créditos descuenta stock y previene duplicados usando allow_multiple; checkout desde carrito requiere confirmación (PR store-redeem-cart-checkout).
- Botón 'Más opciones' en /admin/store permite editar y eliminar productos con modal de confirmación (QA admin-store-options).
- Eliminadas duplicaciones de Bootstrap quitando tabler.min.js y moviendo modales fuera de las tablas (PR admin-dropdown-conflict-fix).
- Historial de compras permite descargar comprobante en PDF y compartir enlace; productos comprados muestran badge "Adquirido" y deshabilitan compra/canje si no se permiten duplicados. Tras comprar o canjear se ofrece descarga directa cuando hay archivo (PR purchased-badge-download).
- Corregido enlace 'Ver en tienda' en manage_store.html a /store/product/<id> para evitar redirección rota (PR admin-store-view-link-fix).
- Mejorada sección de favoritos con botones rápidos, badges y descarga integrada (PR store-favorites-actions).
- Sidebar de tienda muestra categorías dinámicas y filtros rápidos Top/Free/Pack; ruta store_index admite ?top=1, ?free=1 y ?pack=1 (PR store-sidebar-filters).
- Botón de descarga disponible en tarjetas de tienda, favoritos y página de producto si ya fue adquirido (PR store-download-btn).
- Historial de compras filtrable por fecha (7 días, mes actual, 3 meses) (PR purchases-date-filter).
- En edición de productos se sube imagen a Cloudinary y el enlace "Ver en tienda" apunta a /store/product/<id> (PR product-cloudinary-fix).
- Implementado sistema de reseñas y preguntas en productos con filtros en favoritos y visual especial para Packs (PR store-reviews-qa).
- Corregida vista de tienda para mostrar product.image_url con imagen por defecto si falta (PR store-image-url)
- Feed redesign: avatar en formulario de publicación, filtros como pestañas y fechas relativas (PR feed-v1-improved)
- Corregida plantilla store.html para usar product.image si existe, con alt y title; botón "Ver detalle" evita desbordes con tw-whitespace-nowrap (PR store-image-check)
- Added SavedPost model, donation endpoints and mobile nav.
- Añadido soporte de tema oscuro para textos grises en tarjetas del feed (PR dark-text-support).
- Feed principal reorganizado para mostrar solo publicaciones recientes con paginación básica y sin secciones de apuntes (PR feed-wall-redesign).
- Restaurado sistema de pestañas en el feed con secciones dinámicas y etiqueta "📢 Publicación" en lugar de "📝 Apunte" (PR feed-tabs-restore).
- Rediseñada página /trending con vista propia y posts ordenados por likes (PR trending-redesign)
- Vista individual de post ahora incluye botón de compartir y enlace a más publicaciones del autor; se añadió ruta feed.user_posts y se muestran 0 likes por defecto (PR post-page-share).
- Added share buttons, dynamic comments via AJAX and bottom-right toasts with Open Graph meta (PR feed-share-toasts).
- Sidebar right now highlights weekly top posts and shows achievements on mobile; posts include "Ver publicación" button and badge restyled (PR feed-highlights).
- Public profile links now use usernames, new profile page lists notes, posts and achievements, and feed posts include a "Ver perfil" button. Added user notes route (PR feed-profile-links).
- Redesigned public profile with larger avatar, achievements grid and posts/notes sections. Added /perfil/<username>/apuntes route and updated templates to use profile_by_username links (PR public-profile-redesign).
- Fixed public profile template to avoid Jinja 'with' syntax (PR profile-jinja-fix).
- Implemented basic user notification system with model, utility, routes and navbar indicator (PR notifications-basic).
- Added migration for notifications table to fix runtime errors (QA notifications-migration).

- Added quick filter sidebar on feed, PDF preview on upload form, chat messages with timestamps and notifications on comments/messages (PR feed-sidebar-chat-preview).
- Sidebar derecho unificado: apuntes, logros y ranking en una sola card; se eliminó bloque duplicado de logros en el feed (PR sidebar-right-unify).
- Removed mobile duplicate notes/achievements block from feed (PR feed-mobile-cleanup).
- Added weekly missions feature with models, routes, template and navbar link (PR missions-basic).
- Chat page now shows an 'En construcción' message and no longer provides messaging UI (PR chat-placeholder).
- Precios en store.html ahora muestran "S/ 0" cuando el producto es gratuito (PR store-free-price).

- Corrigio plantillas de tienda para usar `product.price` en lugar de `price_soles` evitando UndefinedError (PR store-price-fix).
- Se movió la sección "Últimos apuntes" del feed a /apuntes y se mejoró el sidebar con botones. Las tarjetas de apuntes cargan vista previa PDF usando PDF.js. Productos de la tienda muestran "Desde S/ 0", badge de categoría y botón de compartir (PR feed-store-pdf-preview).
- Implementado sistema completo de ranking y logros con página /ranking, asignación automática y panel admin (PR achievements-ranking-v1).
- Reestructurado el feed con sección de apuntes en la barra lateral, logros con iconos y /trending mostrando publicaciones destacadas de la semana (PR feed-restructure-notes).
- Añadido dropdown de notificaciones con actualización AJAX y botón "Marcar todo como leído" (PR dynamic-notifications).
- Mejora de subida de apuntes: admite imágenes, vista previa y spinner en el botón (PR notes-upload-preview).
- Mejorados filtros rápidos del feed con botones toggle y carga AJAX (PR feed-toggle-filters)
- Added ChatCrunevo page using OpenRouter API, shortcut /notes/populares and share link button on note detail (PR ia-chat-popular-notes).
- Feed principal limpiado quitando secciones de apuntes, logros y ranking; /notes rediseñado como catálogo con tarjetas de vista previa, filtros por likes y ruta /notes/tag/<tag> (PR notes-catalog-redesign).
- SEO meta description actualizada y ruta '/' muestra login o feed seg\u00fan autenticaci\u00f3n (PR root-login-seo-fix).
- Rediseño del feed con barra lateral de iconos, filtros móviles y tarjetas de publicaciones mejoradas (PR feed-redesign-v2).
- Feed index moved to /feed with new sidebar and post card templates (PR modern-feed).
- Corregido view_feed para retornar feed_items y sidebar derecho simplificado (PR feed-view-feed-fix).
- Navbar cleaned removing missions link and verification badge; missions now reside under /perfil with new tab and verification check shown next to usernames (PR profile-missions-verification).
- Mejorada subida de imágenes en el feed con vista previa y spinner; filtros rápidos rediseñados y se eliminó HTML obsoleto al final del feed (PR feed-todo-fix).
- Corregido tamaño del preview de imágenes, se ajustaron las publicadas y se limpiaron restos de HTML en el feed (PR feed-image-preview-fix).

- Verificada ruta view_feed y plantillas para usar solo feed_items sin apuntes extra (QA feed-view-feed-admin-check).
- Filtrado de "apuntes" en FeedItem: el feed y la API ahora omiten notas antiguas incluso para administradores (PR feed-skip-notes).
- Se añadió opción para eliminar publicaciones propias en el feed, removiendo FeedItem y cache (PR post-delete).
- Añadida funcionalidad para que los usuarios eliminen sus propios apuntes desde /notes y /perfil (PR notes-delete-user).
- Botón "Editar" agregado en publicaciones del feed con marca visual (Editado) y control de permisos (PR post-edit).
- Estilo CSS actualizado para centrar imágenes del feed y mejorar visualización móvil (PR feed-image-center).
- Se añadió botón "Reportar" en apuntes y publicaciones con modal y notificación al admin. Se habilitó ruta /notes/edit/<id> para editar título, descripción, categoría y etiquetas (PR note-edit-report).
- Sidebar de /feed/trending simplificado: solo filtros rápidos, formulario de publicación igual al feed y filtros móviles (PR trending-sidebar-cleanup).
- Ajustado ancho de detalle de apunte con container-xl y botón de descarga centrado (PR note-detail-width-fix).
- Actualizado diseño de la tienda con grilla responsiva y tarjetas con borde morado; footer incluye acciones de detalle y compartir (PR store-grid)
- Mejorado layout de tienda y favoritos usando container-fluid, textos truncados con line-clamp y tarjetas pulidas (PR store-layout-polish)
- Nombres de productos con hasta 3 líneas y tamaño 1rem; sección derecha muestra tarjetas de destacados con mensaje vacío y botón "Ver" (PR store-featured-redesign)
- Límite de 3 productos destacados con aviso en add_edit_product y verificación al guardar (PR featured-limit).
- Página de administración de tienda muestra badges de Destacado, Popular, Nuevo y Stock bajo en una columna "Etiquetas" con tooltips. Productos se ordenan por etiquetas (PR admin-store-badges-enhancement).
- Sección de destacados en la tienda convertida en carrusel horizontal con scroll y sin límite de productos (PR store-featured-carousel).
- Eliminado límite de 3 productos destacados en admin; ahora se pueden marcar todos los que se deseen (PR admin-featured-limit-removed).
- Carrusel de destacados movido antes del título de tienda y tarjetas más compactas (PR store-featured-move-reduce).
- Corrección de ordenamiento en admin/manage_store para manejar valores None (PR admin-store-sort-none-fix).
- Mejorado carrusel de destacados con tarjetas modernas, imágenes cuadradas y contenedor con sombra (PR store-featured-card-style).
- Input de imagen del feed usa id "feedImageInput" y contenedor "previewContainer" con vista previa instantánea (PR feed-image-preview-fix).
- Implementado modo oscuro en feed y tienda, scroll infinito e overlay móvil con offcanvas. Añadidas imágenes lazy (PR dark-scroll-overlay).
- Ajustado modo oscuro en tienda y feed: bg-light adaptativo, botones claros y navbar inferior con bg-body (PR dark-mode-fixes).
- Feed mejorado: filtros por categoría, buscador interno y sidebar móvil en offcanvas con botón flotante. Animaciones desactivadas en dispositivos lentos y carga infinita usando categoría. (PR feed-mobile-overlay)
- Corregido include en feed/index.html eliminando 'with categoria=categoria' para evitar TemplateSyntaxError (PR feed-sidebar-with-fix).
- Menú móvil del navbar ahora usa fondo morado con clase `offcanvas-crunevo` y los dropdowns comparten ese color. Botones flotantes de sidebar móvil cambian a icono de filtro y clase `mobile-overlay-btn` (PR overlay-menu-color).
- Tienda muestra precios en destacados, botón "+ Carrito" con AJAX y contador en el navbar y botón flotante (PR store-cart-indicators).
- Fondo del offcanvas m\xc3\xb3vil del navbar ahora cubre todo el cuerpo y enlaces permanecen en blanco; clase ajustada en navbar.html (PR offcanvas-bg-full).

- Menú móvil del navbar actualizado para cubrir toda la pantalla con fondo morado translúcido y texto legible; estilos en navbar.css. (PR mobile-offcanvas-fix)
- Menú hamburguesa y offcanvas del navbar eliminados en móviles; botones ocultos con CSS y marcado retirado. (PR remove-mobile-offcanvas)
- Navbar inferior móvil implementado con mobile_bottom_nav.html e incluido en base.html. (PR bottom-nav-mobile)
- Navbar inferior móvil mejorado con ícono activo, animación de toque y scroll horizontal en pantallas pequeñas (PR bottom-nav-enhanced).
- Altura reducida y tooltips añadidos al navbar inferior, con espacio inferior global para que no tape contenido (PR bottom-nav-improvements).
- Navbar superior ahora se oculta al hacer scroll y reaparece al subir, implementado en main.js y transición CSS (PR navbar-autohide).
- Corregido selector de autohide para '.navbar-crunevo' y botón flotante movido sobre el navbar inferior con bottom:72px (PR overlay-autohide-fix).

- Navbar ajustada a top:0 con CSS y botón de tema añadido en perfil (PR navbar-top-fix-theme).
- Autohide del navbar funciona en todas las vistas y se quitó el botón de tema del navbar, moviéndolo solo al perfil (PR navbar-autohide-mobile).
- Autohide del navbar reescrito para detectar scroll táctil y se limpiaron márgenes globales. Se añadió clase .navbar-hidden (PR navbar-autohide-touch-fix).
- Se añadió página /terms con los Términos y Condiciones y checkboxes obligatorios en registro y subida de apuntes (PR terms-conditions).
- Mejorado formulario de subida de apuntes con categoría, nivel académico, privacidad y etiquetas con sugerencias (PR notes-upload-enhanced).

- wsgi.py importa create_app desde el paquete crunevo nuevamente y se actualiz\xF3 wsgi_admin para mantener consistencia.
- Redesigned note detail with two-column layout, PDF/image viewer via viewer.js and file type detection in notes_routes (PR note-detail-redesign).
- Expanded notes model with language, reading_time, content_type, summary, course and career; upload form modernized with collapse "Más ajustes" (PR notes-upload-form-v2).
- Formulario de publicación ahora usa un modal emergente activado por un botón estilo Facebook en el feed (PR fb-style-modal).
- Refactorizada la sección inferior de los posts con dropdown y reacciones múltiples (PR reactions-ui).
- Sistema de reacciones actualizado con conteo por emoji y compatibilidad móvil (PR reactions-ui-counts).
- Reacciones optimizadas para móviles, con tooltip por emoji y reemplazo de 😎 por 😲 (PR reactions-ui-final).
- Comentarios ahora se abren en un modal con la publicación centrada y las reacciones ordenadas; se eliminó el ícono de corazón (PR reactions-modal-update).
- Manejo de IntegrityError en like_post para evitar fallas de logs por duplicados.
- Corregido template de reacciones convirtiendo sorted_counts a lista para evitar UndefinedError (PR reaction-container-fix).
- Filtros rápidos ocultos en móviles (<=768px) y disponibles solo en el menú flotante azul (PR feed-mobile-filters-hide).
- Reacciones muestran el emoji seleccionado de inmediato y panel accesible con pulsación prolongada; campo "Escribe un comentario..." abre el modal y evita el ícono previo (PR feed-reactions-final-touch).
- Feedback instantáneo al reaccionar: la interfaz actualiza al instante y revierte si falla la petición (PR feed-reactions-ux-instant-feedback).
- Sistema de reacciones final ajustado: un clic agrega o quita, conteo correcto y botón sin estilo visible (PR reaction-toggle-final).
- Reacciones mejoradas: panel 4x2 en móvil, estado del usuario en data-my-reaction y actualización instantánea con reversión (PR reactions-toggle-ux).
- Se evitó que el scroll dispare reacciones; el panel siempre muestra las 8 opciones y se puede volver a abrir sin bloqueos (PR reactions-touch-fix).
- Se ignora el movimiento del cursor o la rueda para evitar reacciones accidentales (PR reaction-scroll-fix).
- Long press fix for mobile reactions: preventDefault en touchstart y umbral de movimiento para mostrar panel correctamente (PR mobile-longpress-reactions-fix).
- Rediseñado el sistema de notificaciones con dropdown claro, íconos por tipo, timestamps amigables y resaltado al abrir (PR notifications-redesign).
- Sistema de comentarios mejorado con carga vía AJAX, enfoque automático en el modal y estilos modernos (PR comments-live-ui).

- Se documenta la hoja de ruta "Mejoras Fase 2": comentarios avanzados, transferencias de créditos, notificaciones ampliadas, logros y ranking, pulido móvil y pruebas de usabilidad.
- Corregido icono de campana en lista de notificaciones usando emoji real para evitar UnicodeEncodeError (hotfix notifications-emoji).
- Ajustado fondo del dropdown de notificaciones a colores neutros con modo oscuro y botón 'Marcar todo como leído' con estilo btn-outline-secondary. Se añadió flecha decorativa (PR notifications-bg-fix).
- Añadida animación pop a los botones de reacciones y en cada emoji del panel (PR reactions-anim-pop).
- Vista previa de imagen muestra spinner de subida en el modal de publicación (PR feed-upload-spinner).
- Filtros rápidos rediseñados como badges con scroll horizontal en móviles (PR feed-quickfilters-redesign).
- Sistema de rachas de inicio de sesión que otorga créditos crecientes cada día (PR login-streak-rewards).
- Recompensa de racha ahora se reclama manualmente con /api/reclamar-racha y widget flotante en el feed (PR login-streak-claim).
- Página /crolars con explicación de la moneda y enlaces desde navbar y footer (PR crolars-info-page).
- Añadido script scripts/generar_misiones.py para insertar misiones en lote.
- compute_mission_states detecta dinámicamente el progreso según code y category (PR mission progress dynamic).
- Perfil muestra misiones con progreso, estado y botón para reclamar créditos manualmente (PR missions-claim-ui).
- Ruta /misiones/reclamar_mision permite reclamar créditos por misión (PR mission-reclaim-route).
- Añadido modelo Referral y pestaña de referidos en el perfil con registro básico en onboarding (PR referral-system).
- Reimplementado endpoint /misiones/reclamar_mision y añadida prueba automática (PR mission-claim-route-test).
- Notificaciones ahora usan tarjetas con íconos por color y filtro rápido; se añadieron estilos y JS para filtrar (PR notifications-cards-filter).
- Se otorgan créditos por referido al confirmar el correo y la pestaña muestra tarjetas con total de créditos (PR referral-rewards).
- Misiones de referidos detectan los completados, nuevos niveles y maratón añadidos. Se premia al invitado con créditos y se desbloquean insignias de "Embajador" y "Aliado". Ranking mensual opcional (PR referral-missions).
- Se agregaron rutas de administrador para eliminar publicaciones y apuntes con notificación al autor y limpieza de feed. La página de reportes permite marcar como resuelto y eliminar posts reportados (PR admin-delete-post).
- Se manejan consultas a Referidos con try/except para evitar errores cuando falta la tabla (PR referral-safe-query).
- Botón 'Eliminar (admin)' en post_card solo se muestra si ADMIN_INSTANCE está habilitado para evitar BuildError (PR admin-delete-post-link-fix).

- Ocultado enlace a /crolars en admin para evitar BuildError (PR admin-crolars-link-fix).
- Renombrado el término 'cr\xc3\xa9ditos' a 'Crolars' en plantillas y mensajes visibles sin cambiar la base de datos (PR rename-credits-crolars).
- Ocultado el menú inferior móvil en la instancia de administración para evitar BuildError al resolver 'feed.feed_home' (PR admin-bottom-nav-fix).
- Botón de carrito y fetch de recuento condicionados a la existencia de rutas de tienda para evitar BuildError en la instancia admin (PR admin-store-route-check).
- Agregadas vistas /admin/misiones y alias /admin/creditos; manage_credits admite filtros por usuario y razón y los usuarios muestran enlace a su historial (PR admin-missions-page).
- Added device token header from localStorage via main.js and stored in auth events (PR device-token-logging).
- Added AdminLog model, comentarios y estadísticas en admin con alerta de reportes urgentes (PR admin-logs-stats).

- Validación de token de dispositivo al reclamar misiones para evitar duplicados y tabla device_claims (PR device-claim-dup-check).

- Added static /cookies page with footer links to cookies, privacidad and terminos (PR cookies-page).
- Botón para eliminar apuntes por admin solo visible si ADMIN_INSTANCE está habilitado para evitar BuildError (PR note-delete-admin-fix).
- Logros ahora otorgan crolars y muestran popup al desbloquear (PR achievements-credits-popup).
- Post cards redesigned with hover effect, reaction panel animation and comment counts (PR post-ui-polish).

- Fixed default boolean in achievement_popup migration using server_default="false" to prevent deployment failure (PR logs-migration-fix).
- Restored comment input below reactions and kept reaction count line unchanged (PR post-comment-input-return).
- Added close listener for achievement popup with fade animations and accessibility tweaks (PR achievement-popup-fix).
- Achievement popup hidden on admin instance, closes properly marking as shown and clearing state with button handler set dynamically (PR achievement-popup-bugfix).
- Popup and window.NEW_ACHIEVEMENTS only load for authenticated users, injecting CURRENT_USER_ID and clearing achievements after successful mark-shown request (PR achievement-popup-login-check).
- Achievement popup only triggered when backend response includes "new_achievement"; DOMContentLoaded check removed and csrfFetch now handles showing popup automatically (PR achievement-popup-runtime).
- Delegated close handler for achievement popup ensuring button works even if regenerated, and removing inline style on close (PR achievement-popup-delegate-close).
- Popup overlay fully hidden with `d-none` when closed and restored on show to prevent blocking clicks (PR achievement-popup-display-fix).
- Achievement popup clears `session['new_achievements']` on mark-shown and `base.html` only defines `NEW_ACHIEVEMENTS` for logged-in users (PR achievement-popup-session-clear).
- Popup shown only once: JS waits for successful mark-shown response before clearing `window.NEW_ACHIEVEMENTS` and base template omits the variable when empty (PR achievement-popup-once).
- Session cleanup reinforced: before_app_request clears `session['new_achievements']` when no pending records and mark-shown logs username (PR achievement-popup-session-cleanup).
- Popup state reset on `beforeunload` and `showAchievementPopup` checks `NEW_ACHIEVEMENTS`; session log prints current value (PR achievement-popup-beforeunload).
- Backend mark-shown endpoint loops through each record and handles errors to ensure achievements are updated (PR achievement-popup-mark-shown-fix).
- Context processor serializes pending achievements and returns an empty list when none to avoid regenerating `window.NEW_ACHIEVEMENTS` (PR achievement-popup-context-fix).
- Context processor syncs session['new_achievements'] and JS clears global variable after marking shown (PR achievement-popup-session-reset).
- Popup now shown on DOMContentLoaded only when NEW_ACHIEVEMENTS has items and mark-shown updates immediately via API (PR achievement-popup-auto-mark)
- Verified new design commit d3b38ae; reviewed templates and CSS, no conflicts detected. make test shows failing BuildError in routes.
- Fixed missing endpoints for navbar links: added legacy aliases for feed and ranking blueprints and updated notifications link (PR feed-route-aliases).
- Fixed indentation in create_app to resolve deployment error (hotfix indentation).
- Updated enhanced_chat_system migration to set booleans using `false` instead of `0` to fix upgrade error (hotfix boolean-migration).
- Sidebar feed links now use tailwind text color classes for better readability (PR feed-sidebar-color).
- Fixed ambiguous join in chat global view to avoid AmbiguousForeignKeysError (hotfix chat-active-users-join).
- Registered Crunebot and saved blueprints for public instance and removed unreachable code; added merge migration to unify heads (hotfix crunebot-blueprint).
- Renamed the assistant blueprint to Crunebot across routes, templates and attachments (PR crunebot-rename).
- Fixed sidebar credits display and search link endpoint to prevent template errors (PR feed-sidebar-credits-fix).
- Updated notes links to use 'notes.list_notes' in bottom nav, sidebar and saved list to avoid BuildError (PR notes-list-alias-fix).
- Fixed bottom nav notifications link to 'noti.ver_notificaciones' and used `|length` for notes count in sidebar (hotfix notifications-link-count).
- Updated profile links to use 'auth.perfil' instead of deprecated 'auth.profile' to avoid BuildError (hotfix profile-link-fix).
- Replaced forum sidebar link with 'forum.list_questions' and wrapped referral ranking query in try/except; achievement session log now uses logger (PR logs-bugfixes).
- Corrected sidebar club link to use 'club.list_clubs' and avoid BuildError (hotfix club-link-fix).
- Fixed sidebar event link and refactored search notes to use existing fields (hotfix search-notes-fields).
- Fixed store links pointing to deprecated endpoints in navbar, feed sidebar and store.html (hotfix store-endpoint-fix).
- Fixed missions sidebar link to use 'auth.perfil' with tab instead of nonexistent 'misiones.index' (hotfix missions-link).
- Fixed AI chat sidebar link to use 'ia.ia_chat' endpoint and avoid BuildError (hotfix ia-chat-link).
- Added aliases for achievements, notifications, onboarding and certificate blueprints to fix ImportError (PR blueprint-alias-fix).
- Corregido feed: eliminado return duplicado, actualizado CSRF en index y enlaces en trending a feed.view_post (PR feed-fix-routes).
- Fixed migration to avoid errors when columns or tables already exist by using `if_not_exists` and `checkfirst=True` (hotfix migration-transaction-failure).
- Removed root '/' alias for auth.login to prevent infinite redirect (hotfix login-loop).
- Updated templates to access current_app via url_for.__globals__ and replaced inspector.has_column with helper in migration (hotfix templates-current_app).

- Replaced `checkfirst` with `if_not_exists` in create_table ops to fix deployment error (hotfix create-table-checkfirst).
- Fixed missing `render_template` import in `__init__.py` causing 500 errors (hotfix render-template-import).
- Added `if_not_exists=True` and `if_exists=True` to `add_courses_system` migration to avoid duplicate table errors (hotfix courses-migration-fix).
- Fixed navbar store link to use 'store.store_index' and avoid BuildError (hotfix navbar-store-link)
- Fixed navbar courses link to use 'courses.list_courses' and avoid BuildError (hotfix navbar-courses-link)
- Fixed notifications dropdown link to 'noti.ver_notificaciones' to resolve BuildError (hotfix notifications-dropdown-link).
- Fixed navbar missions link to use 'auth.perfil' with tab to avoid BuildError (hotfix navbar-missions-link).
- Fixed saved link to use 'saved.list_saved' and corrected notes detail endpoints in templates (hotfix endpoint-fixes).
- Fixed forum link in feed sidebar and profile quick actions to use 'forum.ask_question' (hotfix forum-ask-link).
- Public instance blocks /admin again by using create_app from app and hiding the dropdown link; fixed perfil route user variable, float conversion in store template and saved feed link (hotfix admin-block-route).
- Registered main blueprint and removed redundant home route to restore `main.index` endpoint (hotfix main-blueprint-register).
- Added endpoint checks for footer and error pages to avoid BuildError when blueprints are missing (hotfix endpoint-checks).
- Fixed sidebar links to terms/privacy, trending post includes item context, optional missions list and mobile nav endpoint checks. Added user_level calculation in perfil view (hotfix template-errors).
- Fixed sidebar links: privacy uses 'main.privacidad' and removed obsolete admin.manage_comments link (hotfix template-link-fixes).
- Fixed about link in sidebar to use 'about.about' and avoid BuildError (hotfix about-link-fix).
- Registered courses blueprint and added English path aliases; updated sidebar link (PR courses-aliases).
- Trimmed duplicate content in search/index.html to fix 'block title' error (hotfix search-template).
- Added courses search support and moved search page JS to main.js for single DOMContentLoaded handler (hotfix search-modern)
- Updated feed UI: replaced heart icons with fire, improved filter contrast and lighter gradient background (PR feed-ui-fire-icon)
- Fixed streak claim button to call /api/reclamar-racha and redesigned main navbar:
  centered links, smaller search bar, removed Crunebot link, added theme toggle
  in user menu and softened the "Publicar" button color (PR navbar-streak-fix).
- Fixed navbar template conditional and cleaned ruff errors across routes (PR navbar-template-fix).
- Dark mode improvements: solid dark background, dark search input, sidebar username color and navbar dark style. Trending posts now use the full post card with like/comment/share actions (PR dark-mode-fixes).
- Further dark mode tweaks: override bg-light classes and navbar primary color, ensure textarea and badges adapt to dark theme (PR dark-mode-tweak).
- Fixed dark mode selectors in style.css to target html[data-bs-theme], enabling consistent theme across pages (PR dark-mode-selector-fix).
- Dark mode overhaul: unified dark backgrounds and comment box styles across templates (PR dark-mode-overhaul)
- Feed dark mode: removed gradient background and set solid #0D1117 for feed section (PR dark-feed-solid-bg).
- Fixed remaining dark mode issues: unified body and feed backgrounds, updated card and input styles, and forced text-dark to white (PR dark-mode-bugfix).
- Adjusted feed selectors to use `html[data-bs-theme]` and ensured feed section background stays solid in dark mode (PR dark-mode-feed-css).
- Reemplazadas plantillas de publicaciones con 'components/post_card.html' y eliminado diseño anterior y la clase hover-scale (PR post-card-modernization).
- Added /health endpoint in wsgi.py and updated fly.toml to check it via HTTP (PR fix-health-check).
- Restored admin.logs and product_history routes to fix BuildError
- Simplified health endpoint to return plain tuple as instructed (PR fix-health-return).
- Removed references to deprecated admin.manage_store endpoint, linking to PUBLIC_BASE_URL/store instead (hotfix admin-store-links).
- Registered static_pages blueprint to enable /cookies page and added /events alias to /eventos with updated sidebar link (PR events-cookies-fix).
- Navbar redesigned: centered search bar, mobile modal search, trending links updated in sidebar and ranking hero (PR trending-navbar-update).
- Prevented BuildError in templates by checking 'feed.view_feed' exists before linking (hotfix feed-link-check).
- Fixed links to 'notes.list_notes' in navbar and sidebar templates with endpoint checks to avoid BuildError on admin instance (hotfix notes-sidebar-link).
- Unified AI chat under /ia and removed /crunebot routes and templates; /crunebot now redirects to /ia (PR ia-chat-unification).
- Ocultado navbar y navegación inferior en login y registro; se calcula padding superior dinámico con JS para la navbar fija (hotfix login-navbar-padding).
- Verificado enlace al foro en navbar, feed sidebar y club list con comprobación de endpoint para evitar BuildError (hotfix forum-link-check).
- Moved 'Ver tendencias 🔥' button from hero to ranking tabs next to 'Top Referidores' and styled as nav-link (PR trending-button-move).
- Redirected main.index to admin dashboard when ADMIN_INSTANCE and guarded store and stats links to avoid BuildError (hotfix admin-root-builderror).

- Restored /admin/credits routes and export CSV to fix BuildError (hotfix manage-credits-route).
- Fixed comment modal to display complete post detail via new /feed/api/post endpoint and ensured closing works correctly (PR comment-modal-full-post).
- Added environment variable overrides in create_app and implemented admin delete routes. Fixed missing csrf_field in club detail. Migrations use if_not_exists and safe drop to avoid errors.
- Wrapped admin sidebar link to 'admin.manage_achievements' with endpoint check to avoid BuildError when route is absent (hotfix admin-sidebar-achievements).
- Imported reactions macro in _post_modal.html to fix UndefinedError (hotfix reactions-import).
- Fixed dashboard template variable names to match admin route and replaced stats.users usage with new_users_week (hotfix admin-dashboard-stats).
- Redesigned comment modal using feed post card layout and fixed share modal backdrop removal (PR share-modal-redesign).
- Updated IA route to use OpenRouter chat completions API, added OPENROUTER_API_KEY config and CSP connect-src entry (PR openrouter-api-fix).
- Added admin.run_ranking route invoking calculate_weekly_ranking and linked from dashboard (hotfix admin-run-ranking-route).
- Updated IA route headers to include Content-Type and switched model to "deepseek-chat" via OpenRouter (PR deepseek-openrouter).
- Improved IA route error handling and added extra padding to chat messages to avoid footer overlap (PR deepseek-openrouter-ui-fix).
- Added HTTP-Referer and X-Title headers when calling OpenRouter to satisfy API requirements (hotfix openrouter-headers).
- Fixed manage_users links to avoid BuildError when admin endpoints are missing (hotfix admin-user-links).
- Adjusted IA referer header fallback to request.url_root and added OPENROUTER_MODEL config (hotfix openrouter-referer-model).
- Guarded Crunebot button and route on admin instance; restored admin store alias and verification routes; updated migrations with existence checks (PR admin-crunebot-fix).
- Fixed TemplateSyntaxError in club list and added safety checks in migrations (PR template-migration-fixes).
- Replaced OpenRouter integration with direct OpenAI ChatCompletion API and updated config, requirements and .env (PR openai-integration).
- Updated ia_routes to use new openai.chat.completions API and fix crash (hotfix openai-api-call).
- Improved chat layout: added footer padding, dynamic year and footer styling (PR chat-footer-fix).
- Added CreditReasons.ACTIVIDAD_SOCIAL constant, handled OpenAI RateLimitError in ia_routes and skipped migration test when SQLite lacks IF NOT EXISTS support (hotfix social-credit-constant).
- Store index uses Bootstrap carousel for hero, ofertas and premium blocks; product cards show first_image or default placeholder, navbar displays cart icon with badge and JS calls /store/api/cart_count (PR store-carousel-fixes).
- Unified store carousel height, squared product images and improved dark mode styles (PR store-ui-consistency).
- Replaced IP rate limit on login with per-user attempt tracking using Redis or memory cache, showing countdown on the login page (PR login-attempt-limit).

- Replaced notes sidebar in notes list with modern feed sidebar and adjusted layout (PR notes-modern-sidebar).
- Added trending posts section to feed sidebar with weekly top posts (PR feed-sidebar-trending).
- Added settings page '/configuracion' with authenticated route and sidebar. Updated user dropdown with copy, edit and configuración options (PR settings-page).
- Removed copy and edit options from user dropdown and related JS listener (PR profile-menu-cleanup).
- Added password change form and backend route under settings (PR settings-change-password).
- Fixed logout event logging using _get_current_object and added test for logout event.
- Split personal settings into separate username and description forms with real-time availability check and page reload on success. Updated profile header to show username overlay on banner (PR settings-username-fix).
- Cleaned feed left sidebar: removed trending posts and added link card (PR feed-sidebar-cleanup).
- Styled feed sidebar trend card with bi-fire icon before text (PR feed-sidebar-fire-icon).
- Diagnóstico de carpeta components realizado; listado de archivos y detección de duplicados funcionales. Se sugirió refactorización (QA components-diagnosis).
- Unificada la barra lateral del feed, eliminando la versión duplicada y actualizando las vistas a usar components/sidebar_left_feed.html (PR feed-sidebar-unify).
- Introducida cola de tareas con RQ y worker para insertar publicaciones de feed asincrónamente; create_feed_item_for_all ahora encola la tarea (PR feed-queue-worker).

- Consolidated script initialization: moved DOMContentLoaded handlers from feed.js, notifications.js, share.js and chatia.js into main.js; modules expose init functions (PR unify-js-entry).

- Removed "Misiones" link from navbar, added mobile offcanvas sidebar toggle, redirected /register to onboarding and relaxed password policy to 6+ chars with letters and numbers (PR mobile-sidebar-register-fix).
- Removed duplicate 'reportlab' entry from requirements.txt (PR requirements-cleanup).
- Moved login/register theme and countdown scripts, admin table datatables and navbar search logic into main.js; templates now use data attributes and initAuthPage/initNavbarSearchLegacy (PR domloaded-refactor).
- Added user-facing club creation route, form template and updated sidebar button (PR create-club-route).
- Added test for '/health' endpoint asserting 200 response (PR health-endpoint-test).
- Corregido formulario de reseña en view_product.html eliminando repetición de 'Comentario' y texto 'div>' sobrante.
- Replaced print statements in crunevo/utils/image_optimizer.py with logging and added logger import (PR image-logging-fix).
- Fixed profile header overlay by raising username z-index and moving styles to perfil.css. Computed club and mission counts in auth.perfil, showing participation percentage (PR profile-fixes).
- Improved chat: sanitized messages, active user ping with Redis fallback, real-time UI updates and message button on profiles (PR chat-enhancements-phase1).
- Added dynamic link previews for pasted URLs using BeautifulSoup and Redis cache (PR link-preview).
- Refined mobile sidebar toggle button with fixed 48px circle and removed excessive click area (PR mobile-menu-button-fix).
- Added graceful fallback to in-memory task queue when Redis unavailable (PR redis-fallback).
- Wrapped ranking sidebar links with endpoint checks to prevent BuildError on admin instance (hotfix ranking-sidebar-link).

- Improved error templates: centered with limited width, added close button and responsive wrapper (PR error-page-responsive).
- Fixed club post creation form to import csrf macro and use csrf_field() (hotfix club-csrf).
- Adjusted footer colors for dark theme, ensuring readable text and subtle border (PR dark-footer-fix).
- Wrapped IA chat link in feed sidebar with endpoint check and added /favicon.ico route to serve static icon (hotfix ia-sidebar-favicon).
- Reemplazado formulario en el feed por botón que abre modal de creación con opciones de imagen, video, apunte o foro. Formulario usa POST a /feed y botón se habilita solo con contenido. (PR feed-post-modal)
- Añadida ruta '/feed/post' para aceptar POST y modificado index del feed con caja de entrada y modal de publicación tipo Facebook. (PR feed-post-overlay)
- Rediseñado input rápido del feed con botones visibles de Live, Foto/Video y Apuntes; botón Foto/Video abre el modal y selecciona imagen automáticamente. (PR feed-input-redesign)
- Wrapped trending links with endpoint check to prevent BuildError when feed routes are missing (hotfix feed-trending-link).
- Activado botón 'Publicar' si hay texto o archivo en el feed (hotfix feed-post-button).
- Wrapped notes upload quick action link with endpoint check and added favicon files (hotfix notes-upload-link).
- Permitir múltiples imágenes en el modal de publicación con vista previa y botón de eliminar fijo. (PR feed-multi-image)
- Added /notifications/api/count endpoint and updated mobile badge script with error handling (PR notifications-count-fix).
- Implemented profile page improvements: repositioned username header, added real recent activity feed, new sidebar cards and tooltips. (PR perfil-enhancements)
- Solucionados warnings de autofocus oculto, soporte Safari de backdrop-filter y fuentes en CSP (PR accessibility-fixes).
- Eliminado script en index del feed para usar feed.js y evitar vistas duplicadas; se habilitan publicaciones solo texto (PR feed-final-polish)
- Corrigido preview de imágenes en el feed eliminando lógica duplicada en main.js y
  añadiendo aria-label al botón de borrar. Se ajustó la sección de estadísticas
  del perfil con layout horizontal scrollable. (PR profile-feed-fix)
- Habilitada verificación con tooltip en perfil, removida tarjeta redundante y menú móvil ajustado más arriba. Vista previa de imágenes evita duplicados y botón de eliminar no dispara doble acción. (PR feed-profile-adjustments)
- Fixed SQLAlchemy case usage in search routes, replacing func.case with case to avoid TypeError logs (PR search-case-fix).

- Removed unused `perfil_sidebar.html` after verifying no includes or routes reference it. (QA perfil-sidebar-diagnosis)
- Adjusted verified badges in feed posts to check `verification_level >= 2` and added tooltip. Removed duplicate image preview initialization in main.js. (PR feed-verify-fix)
- Wrapped forum quick action link with endpoint check to avoid BuildError when forum routes are missing (hotfix forum-ask-link).

- Displayed verified badge in own profile page using same markup as post cards and checking `verification_level >= 2`. (PR perfil-own-verify)
- Moved username header with verification badge above description without interfering with avatar. (PR perfil-username-check)
- Fixed feed form button enabling for text-only posts by adjusting feed.js textarea handler and removing default disabled attribute. (hotfix feed-text-posts)
- Repositioned profile stats below username on desktop with responsive duplication. (PR perfil-stats-below)
- Cleaned profile header layout removing stats block, hiding sidebar numbers on /perfil and improving modal text post validation. (PR perfil-layout-cleanup)
- Positioned username overlay with dark background over banner on desktop. (hotfix perfil-username-overlay)
- Reorganized profile header placing username next to avatar on desktop and showing stats in a gray block. (hotfix perfil-header-restore)
- Improved email confirmation logging and resend feedback; send_email returns detailed errors and register links to reenviar (PR email-resend-debug)
- Eliminada vista central de stats en perfil, mostradas en la barra lateral con puntos, crolars y apuntes como en el feed. Portada reducida y margen ajustado para mostrar el nombre sin superposición; columna principal centrada en móviles (PR perfil-sidebar-restore).
- Sanitized recipient handling in `send_email` ensuring Resend receives a list of addresses (PR resend-to-list-fix).
- Ajustado nombre de usuario a la izquierda en móviles dentro de perfil y descripción centrada. (PR perfil-mobile-name-align)
- Mostrar múltiples imágenes en cada tarjeta de publicación con galería modal y estilos en feed.css. (PR feed-gallery-display)
- Añadido enlace para cambiar email en pending.html debajo de 'Volver al inicio' (PR pending-change-email-link).
- Validación de formato de correo en /onboarding/register y prueba unitaria correspondiente (PR email-format-validation).
- Mejorado diseño del correo de confirmación con imagen, botón con sombra y pie responsive (PR confirmation-email-design).
- Añadido flujo de eliminación de cuenta con botón en configuración, ruta protegida y test (PR delete-account).
- Corregido enlace en pending.html para usar 'onboarding.register' y evitar BuildError (hotfix pending-register-link).
- Reestructurado sistema de imágenes en feed con componente unificado y galería navegable (PR feed-gallery-rework).
- Galería del feed rediseñada con cuadrícula dinámica, modal con contador y unificación de file_url como imágenes (PR feed-gallery-facebook-style).
- Reemplazado image_gallery.html y modal global con diseño tipo Facebook, nuevas clases y funciones JS simplificadas (PR feed-gallery-ui-fix).
- Rediseñado el feed principal con tarjetas centradas "feed-post-card" y oculto el sidebar derecho en móviles (PR feed-facebook-style).
- Galería de publicaciones adaptada con clase `.post-gallery`, navegación por publicación y padding reducido en móviles (PR feed-gallery-grid).
- Eliminado Redis por completo; caches ahora usan memoria y se actualizó README y pruebas (PR redis-removal).
- Galería del feed ajustada con límite de altura 300px, cuadrícula de hasta cuatro miniaturas y overlay de más imágenes; modal lee URLs desde data attribute (PR feed-image-grid-fix).
- Incluido feed.css globalmente en base.html para activar la cuadrícula de la galería en todas las vistas (PR feed-gallery-css-fix).
- Ajustados estilos del feed: imágenes del modal preservan proporciones, tarjetas ocupan todo el ancho y márgenes móviles eliminados (PR feed-responsive-fixes).
- Convertido generador a lista en image_gallery.html para mantener JSON del modal. (PR gallery-list-fix)

- post_card.html now uses a local `author` variable and shows 'Usuario eliminado' when missing (PR post-card-orphan-fix).
- Updated profile tabs to use query string navigation, ensuring missions and achievements load correctly (PR perfil-tabs-fix).
- Fixed edit and delete actions on feed posts with modal form and fetch logic (PR feed-edit-delete-fix).
- Resolved feed.js syntax error and exposed post action functions to window (hotfix feed-js-buttons).
- /health endpoint now returns JSON {"status": "ok"}; updated test accordingly (PR health-json-endpoint).
- Fixed deleting posts with saved records; removal now deletes SavedPost entries to prevent IntegrityError (PR delete-savedpost-fix).
- Implementado visor de imágenes con URL dinámica tipo Facebook y navegación en feed.js y base.html (PR photo-modal-dynamic).
- Rediseñado modal de imágenes estilo Facebook con botones accesibles, tarjeta informativa y ruta compartible "/feed/post/<id>/photo/<n>" que establece OG:image (PR photo-modal-redesign).
- Añadidos metadatos OpenGraph dinámicos en `post_detail` con título y descripción derivados del contenido, enviados desde `feed_routes.py` (PR feed-og-tags).
- Se extrajo el CSS del visor de imágenes a `photo-modal.css`, se incluyó en `base.html` y se añadieron mejoras de accesibilidad: role="dialog", botones type="button" y enlace para abrir la imagen en nueva pestaña. (PR photo-modal-css)
- Galería macro ahora siempre define data-images para todas las publicaciones y trending incluye botón "Volver al Feed" (PR feed-gallery-data-images).
- Mejorado visor de imágenes con fondo oscuro, controles de zoom y flechas centradas. Tarjeta lateral ocupa 100% hasta 400px y botón para abrir imagen en nueva pestaña. (PR photo-modal-pro-style)
- Separación de plantillas escritorio/móvil para el feed con detección de user-agent y script de recarga. (PR mobile-desktop-separation)
- Added PWA manifest and service worker with offline caching; registered in base.html (PR pwa-support).
- Updated service worker caching: removed '/feed', excluded JS from dynamic cache and bumped version to crunevo-v2 (PR pwa-cache-update).
- Pending email confirmation page redesigned with gradient background, modern card and bouncing envelope icon (PR pending-ui-refresh).
- Fixed duplicate isMobile constant in main.js that prevented feed buttons from working (PR feed-buttons-bugfix).
- Implemented route `onboarding.change_email` with new template and updated pending page with disabled resend button (PR pending-change-email-route).
- Updated onboarding confirm page with modern card, email change and AJAX resend endpoint; added `/auth/resend-confirmation` route (PR confirm-resend-change).
- Onboarding now redirects to feed after email verification, profile completion is optional with default bio text when empty (PR optional-onboarding-fix).
- Onboarding finish page updated with modern card, dynamic avatar preview and bio counter (PR onboarding-finish-refresh)
- Added /api/user endpoint returning activation status and JS redirect in pending.html to avoid being stuck after verification (PR pending-verify-redirect).
- Ensured email confirmation logs the user in after activation to refresh session (PR confirm-login-user).
- Pending page now polls `/api/user` every few seconds and redirects once the account is activated to avoid getting stuck (PR pending-refresh-status).
- Mejorado visor de imágenes del feed con fondo oscuro, zoom accesible y flechas internas al estilo de redes sociales (PR photo-modal-advanced).
- Added real-time online user count with Flask-SocketIO; navbar shows dynamic badge (PR online-count-socket).

- Added bounce/fade animations for mission status changes and achievement cards with unified DOMContentLoaded handler (PR mission-achievement-animations).
- Added weather widget on user dashboard fetching data from OpenWeather API with caching via requests. (PR weather-dashboard-widget)
- Añadido sonido opcional para nuevas notificaciones con control en configuración (PR sound-notifications).
- Added keyboard shortcuts Shift+H (home) and Shift+N (new post) with a help dialog accessible from a question icon. (PR keyboard-shortcuts-help)
- Added quick-notes modal with Shift+Q shortcut storing notes in localStorage. (PR quick-notes-modal)
- Fixed OnlineNamespace.on_disconnect to accept optional sid and avoid TypeError causing worker restarts (PR socketio-disconnect-fix).
- Gunicorn now uses the eventlet worker and SocketIO async_mode is set to eventlet to prevent timeouts. (PR socketio-eventlet-worker)
- errors blueprint registered once in create_app for admin and public modes (PR errors-blueprint-once).

- Config class now logs DB URI with logging.getLogger when DEBUG is enabled (PR config-debug-log)
 
- Added TwoFactorToken model with 2FA login flow and backup codes. (PR twofactor-auth)
- Added MAINTENANCE_MODE flag with admin toggle and maintenance blueprint (PR maintenance-mode).
- Added VerificationRequest model with admin approval workflow and profile badges. (PR verification-requests)
- Added UserActivity model tracking posts, comments and logins with new dashboard activity page. (PR user-activity-tracking)
- Added weekly database backup job uploading to S3 via apscheduler (PR db-backup).
- SiteConfig table stores MAINTENANCE_MODE loaded on startup (PR maintenance-db-flag).

- Dashboard charts now use real registration and content metrics; docs added (PR admin-dashboard-metrics).
- Added PageView model to log requests and admin heatmap analytics (PR pageview-analytics).
- Chat ahora admite mensajes de audio cortos en formatos MP3/OGG con validación de duración y subida a Cloudinary o carpeta local (PR chat-audio-support).
- Widget de apuntes embebible con ruta /notes/<id>/embed y botón de copiado en detalle (PR notes-embed-widget).
- Consolidated DOMContentLoaded handlers from courses, events and private chat into main.js (PR domcontent-consolidation).
- PageView logging commits after each request and skips health endpoints (PR pageview-commit-after-request).

- Patched eventlet websocket close to ignore EBADF and prevent noisy 'Bad file descriptor' logs (PR websocket-ebadf-fix).
- Added tests for PageView logging, admin pageviews analytics and maintenance mode persistence (PR pageviews-maintenance-tests).
- Cleared stale flash messages on email confirmation (PR confirm-flash-clear).
- Auth routes now verify the `two_factor_token` table exists before using TwoFactorToken to prevent login failures when migrations are missing (PR twofactor-table-check).
- Consolidated DOMContentLoaded handlers from store/store.html, chat/global.html, ia/chat.html and dashboard/_weather.html into main.js (PR domcontent-store-chat).
- Added test ensuring users can access the feed after confirming their email (PR confirm-feed-access-test).
- Added automatic note categorization suggestions when uploading notes (PR note-categorizer).
- Posts now support a `comment_permission` setting (`all`, `friends`, `none`) with forms and comment endpoint enforcing it (PR comment-permission).
- Introduced Story model with expiry, /stories routes and scheduled cleanup (PR stories-feature).
- Onboarding confirm route refreshes user before login to fix feed redirect issue (PR confirm-login-refresh).
- Events now include notification_times and recurring; calendar JSON endpoint and missions auto-activate before linked events (PR events-calendar-missions)
- Fixed is_active column migration using server_default=sa.text('true') to avoid PostgreSQL type mismatch (PR mission-boolean-default-fix).
- Added migration ensuring two_factor_token table is created if missing (PR twofactor-migration-fix).
- Migration fix for comment_permission column using op.add_column with if_not_exists (PR comment-permission-migration-fix)
- Added fullscreen toggle and annotation hook in viewer.js with button in note detail (PR note-viewer-fullscreen)
- Added GroupMission model with shared progress and UI elements for group objectives (PR missions-group-objectives).
- Added UserBlock model with chat blocking and attachment uploads for images and files (PR user-blocks-attachments).
- Purchase model now stores optional shipping address and message; checkout form collects them (PR purchase-shipping)
- Added PrintRequest model with /notes/<id>/print queue and admin tools to mark prints as cumplidos (PR notes-print-queue)
- Comments admit anonymous posting stored as pending; admin queue allows approving or rejecting them (PR anonymous-comment-review)
- Added optional video conference URLs on events with Jitsi/Zoom embed (PR event-video-links).
- Added note translation helper using Google Translate API with language switcher in viewer (PR note-translate-switcher)
- Added scheduled cleanup job for inactive posts with admin-configurable retention days (PR inactive-post-cleanup)
- Integrated Sentry error monitoring with logging integration and setup docs (PR sentry-monitoring)
- Added local SHA-256 hashing on note uploads to detect duplicates, blocking the upload and notifying moderators (PR note-plagiarism-check).
- Added OAuth import from Google Drive and Dropbox allowing file import to notes (PR drive-dropbox-import).
- Exposed read-only API endpoints with rate limiting and added developer API key generation (PR developer-api-endpoints).
- Added `career` and `interests` fields to users with notifications filtered by these attributes (PR user-career-interests).
- Added LinkedIn sharing and posting for certificates with OAuth integration (PR linkedin-share)
- Added Internship model with application routes and filters by field/location (PR internship-system).
- Generated PDF invoices after each purchase and added profile tab to download them (PR invoice-download).
- Shortened Alembic revision ID to `user_block_attachment` and updated dependencies to fit varchar(32) limit (PR revision-length-fix).
- Dropped leftover sequence before creating `user_block` table to avoid UniqueViolation on repeated migrations (PR user-block-sequence-fix).
- Admin prints and comments now link to PUBLIC_BASE_URL/notes/<id> since notes blueprint isn't loaded in admin.
- Fixed invoice path resolution using current_app.root_path to avoid FileNotFoundError when downloading receipts (PR invoice-path-fix).
- Renamed PersonalBlock.metadata column to _metadata with property and fixed mobile navbar store link (PR personal-block-metadata-fix).
- Added Tailwind utility classes to personal space templates and ensured formatting/tests pass (PR personal-space-tailwind-fix).
- Dropped leftover sequence before creating `personal_block` table to avoid UniqueViolation errors (PR personal-block-sequence-fix).
- Patched RFC6455WebSocket.close to ignore EBADF errors and remove remaining "Bad file descriptor" logs (PR websocket-rfc6455-fix).
- Forzamos login con force=True en la ruta de confirmación para evitar sesiones desactualizadas y redirecciones al pending. (PR confirm-force-login)
- Added test to ensure only success flash after email confirmation and no pending redirect (PR confirm-feed-flash-test).

- Reordered sidebar item "Mi Espacio Personal" under "Mi Perfil" and centered profile icon on mobile navbar while removing "Buscar" and "Mi Espacio" links (PR mobile-nav-sidebar-reorder).
- Implemented comprehensive 'Mi Carrera' module with career-filtered posts, notes, courses, clubs, events, chat and featured students tabs, with JS and CSS integration (PR career-module).
- Fixed Replit gamification feature errors, restored sidebar template, removed empty migration and ensured tests pass (PR replit-gamification-fixes).
- Handled missing crolars_hall_member table with get_hall_membership helper and template update (PR hall-membership-safe).
- Added table_exists helper and login requirement to activated_required; routes skip queries if tables are missing (PR log-error-fix).
- Relaxed default Flask-Limiter to 1000/day and removed limits from store and developer routes, keeping limits only on login and onboarding (PR rate-limit-tweak).
- Improved email confirmation flow: activated_required refreshes user from DB, added 429 error page, and removed 'Mi Espacio' from mobile nav (PR email-activation-fix).
- Added missing templates for Ghost Mentor challenge and League team creation; fixed backpack template when table missing (PR log-fixes-templates).
- Fixed optional alias update to avoid NULL username and added /onboarding/confirm page with redirect after register. Updated test expectations (PR register-confirm-redirect).
- Onboarding confirm ahora redirige a /onboarding/finish si el perfil usa datos por defecto y se actualizan las pruebas (PR onboarding-finish-redirect).

- Actualizado correo de confirmación indicando que el enlace es válido por 1 hora (PR confirm-link-validity).
- Finish route activates user and refreshes session to prevent stuck pending state (PR onboarding-finish-activate-login).
- Finish route refreshes user and clears flashes; added test ensuring feed access after completing profile (PR finish-refresh-test).
- Fixed UnboundLocalError in onboarding register GET by only sending email after POST and returning template on GET (PR register-user-fix).
- Mobile bottom nav store link uses fallback to "/" when store blueprint missing to prevent BuildError (PR store-link-fallback).
- Mobile bottom nav and navbar career links use fallback to '/micarrera' when the career blueprint is missing (PR career-link-fallback).
- Enhanced personal space with Notion-style notes, Trello-style tasks and dashboard metrics (PR personal-space-workspace).
- Activated and fixed personal space: suggestions create blocks, initial template via "Comenzar" button, dark mode syncs with global theme and API routes require activated login (PR personal-space-activation).
- Focus mode hides navbars and sidebars, includes floating exit button (PR focus-mode-ui).
- Suggestion buttons now redirect to personal_space.create_goal and personal_space.create_kanban routes instead of creating blocks directly (PR personal-space-suggestions-routes).
- Confirmed personal_block table represents personal_space; no additional model added (PR personal-space-schema-review).
- Added API tests for creating, updating, deleting and reordering personal space blocks (PR personal-space-api-tests).
- Documented personal space dashboard and shortcuts in README (PR docs-personal-space-dashboard).
- Added recommended_products variable in store.view_product to fix template error and show related products (PR store-recommend-fix).
- Fixed undefined csrf macro in store.html and added missing imports in duel, event and poll routes (PR csrf-macro-fix).
- Imported csrf macro in view_product.html to fix template error (PR store-view-product-csrf-import).
- Extracted inline JS from store/store.html to static/js/store.js and loaded via extra_js block (PR store-js-extract).
- Moved sidebar filter markup into #filterOffcanvas with a floating button on mobile; off-canvas styles and JS toggling added (PR store-filter-offcanvas).
- Added advanced filters with price range slider, stock checkbox, tag list and AJAX refresh (PR store-advanced-filters).
- Implemented store.search_products API with AJAX search and infinite scroll; removed 'Cargar más' button (PR ajax-store-search).
- Implementado sistema de solicitudes de productos con modelo ProductRequest, formulario para estudiantes y panel admin de aprobación. Botón flotante en tienda para solicitar. (PR store-product-requests)
- Added dark-mode variables in store.css and updated components to use them, ensuring theme toggle works (PR store-dark-mode).
- Precios en soles estandarizados y visibles solo si product.price > 0 en plantillas de tienda (PR store-price-standard)
- Ajustadas reglas de .product-image y contenedor para que las imágenes se mantengan cuadradas con object-fit: cover (PR product-image-square).
- Importación de macro CSRF añadida en store.html para evitar UndefinedError (PR store-csrf-import-fix).
- Reviewed redesigned marketplace; tests passed (116) and functionality stable. Suggest optimizing CSS/JS size and modularizing store.js (PR store-design-review).
- Fixed store.css not loading by using head_extra block and removed stray </meta> tag in store.html (PR store-css-load-fix).
- Restored product grid layout, limited card width to 320px and corrected cart count endpoint (PR store-grid-js-fix).
- Mejorada accesibilidad del marketplace: botones con íconos tienen title, campos de dirección con placeholder y overlays usan role="button" (PR accessibility-html-fix).
- Exposed openProductRequestModal and clearAllFilters on window to avoid ReferenceError when used inline (PR store-js-global-functions).
- Added note to README explaining how to resolve Fly.io warning about the app not listening on 0.0.0.0:8080 (PR fly-port-doc).
- Clarified troubleshooting steps for the Fly port warning, suggesting `fly logs -a crunevo2` to verify Gunicorn starts (QA fly-port-troubleshoot).
- Sidebar in store page can be collapsed with a new button, hero header removed and product grid shows up to 5 items per row (PR store-collapse-sidebar).
- Permite publicar productos desde la tienda con modal y ruta /store/publicar-producto; productos se crean con is_approved=False (PR store-user-publish).
- Added gradient header and basic tab navigation for Mi Carrera; initialization moved to main.js to avoid extra DOMContentLoaded listener (PR career-header-fix).
- Moved publish product button to header and fixed store initialization for sidebar toggle (PR store-publish-btn-pos).
- Restored /admin/store management view and added user actions (historial, rol y activación). Mobile nav se oculta en modo admin para evitar 404 de notificaciones (PR admin-panel-fixes).
- Fixed Mi Carrera header gradient visibility in light mode, added dark theme styles and footer now adapts to theme automatically (PR career-header-gradient-fix).
- Backpack routes now check table_exists to avoid errors when tables are missing (PR backpack-table-check).
- Fixed store.js initialization block and moved sidebar toggle button next to page title; added extra_js block in base template (PR store-js-init-fix).
- Updated career header gradient and dark-mode footer styles; defined new CSS tokens (PR career-footer-style-fix).
- Permitidas compras repetidas en la tienda eliminando el bloqueo "Ya lo tienes" y mostrando aviso informativo (PR store-rebuy-allow).
- Tarjetas uniformes con flexbox y espacios reducidos; botón anclado y textos compactos (PR store-card-spacing).
- Filtro de precios ahora usa rango doble hasta S/10,000 y botón "Aplicar filtros" para ejecutar búsqueda (PR store-filter-range-btn).
- Reinstated edit_product route in admin panel to fix manage_store errors (PR admin-edit-link-fix).
- Added desktop application launcher menu with grid icon, links to profile, personal space, missions, ranking, league, backpack and challenges; CSS and JS integrated (PR desktop-launcher-menu).
- Added missing backpack templates (journal, new_entry, view_entry) to fix TemplateNotFound errors (PR backpack-templates-fix).
- Fixed mobile header overlap, restored notes icon in bottom nav and improved notification filters for responsiveness (PR mobile-visual-fixes).
- Rediseñadas /onboarding/pending y /onboarding/change_email con tarjeta centrada e íconos Bootstrap (PR onboarding-pages-redesign).
- Mejorados formularios de verificación y botones flotantes reposicionados sobre la barra inferior (PR onboarding-floating-fix).
- Tarjetas del feed sin 'Vista rápida' y apuntes con Vista Rápida y botones unificados (PR notes-feed-card-fix).
- Mejorado perfil con carga de avatar y vista previa; botón flotante "Guardar cambios" y nueva ruta /perfil/avatar (PR profile-avatar-preview).
- Fixed notes list template to avoid Jinja 'with' syntax using variable assignment (QA notes-list-jinja-fix).
- Updated 429 error page to fallback to '/' when 'feed.feed_home' route is missing, preventing BuildError (QA 429-feed-link-fallback).
- Foro usa Quill.js para formato enriquecido e imágenes subidas a Cloudinary; preguntas y respuestas guardan HTML limpio (PR forum-rich-editor).
- Galería de imágenes del feed adaptada: primera imagen grande y cuadrícula responsiva para el resto; CSS ajustado (PR feed-gallery-responsive).
- Perfil mejorado: botones de avatar y banner con previsualización y estadísticas completas (PR profile-banner-fixes)
- Added test ensuring /notes loads correctly with updated include syntax (QA notes-page-test).
- Feed gallery fully redesigned for responsive grids and like icon now uses `bi-fire` by default (PR fire-icon-gallery-fix).
- Gallery layout polished with adaptive heights and overlay for extra images using new two-images/four-images classes (PR feed-gallery-polish).
- Unified gallery item border-radius and added cursor pointer on overlays (PR feed-gallery-tuning).
- Improved gallery overlay condition for 5+ images, pointer cursor and modal navigation via window key events (PR fb-gallery-modal-fix).
- Fixed modal navigation index handling and added missing image alt attributes (PR gallery-modal-index-fix).
- Updated main.js selector so photo routes load correctly with new gallery classes (PR gallery-modal-selector-fix).
- Ensured gallery images stretch properly and modal selection stays within each post (PR gallery-layout-fix).
- Added grid-row rules for post-image-grid to avoid collapsed layouts (QA post-image-grid-rows).
- Fixed multi-image preview layout and ensured modal only shows images from the selected post (PR gallery-preview-fix).
- Ajustada altura de .facebook-gallery con aspect-ratio para evitar recortes de imagenes en escritorio (PR gallery-aspect-ratio-fix).
- Uniformizado collage de imágenes del feed con aspect-ratio y grid-auto-rows; las imágenes se adaptan sin dejar espacios grises (PR feed-gallery-consistent).
- Galería ahora detecta orientación de imágenes al haber dos fotos y aplica clases `.two-horizontal` o `.two-vertical` para evitar recortes (PR gallery-orientation-detect).
- Improved accessibility: added alt text to various images, aria-labels to icon-only buttons and removed gray background from `.facebook-gallery` (PR accessibility-alt-labels).
- Galería ajustada como Facebook: dos verticales lado a lado, preview máximo 5 imágenes con overlay '+X' (PR fb-gallery-improve)
- Multi-image layouts now adapt height automatically without forced aspect ratio (PR gallery-auto-height)
- Talisman ahora no fuerza HTTPS en modo de pruebas para evitar redirecciones (task feed fix).
- Restored base.html to fix blank feed after redesign (PR feed-base-restore).
- Unificada carga de posts en /feed usando un solo template moderno y API HTML (PR feed-post-unify).
- Limpieza de plantillas del feed: eliminado feed_mobile, list.html y CSS antiguo. feed_routes usa solo feed/feed.html. (PR feed-templates-cleanup)
- Revisado feed por duplicados y añadido console.log de currentPage en feed.js (PR feed-duplicate-debug).
- Corregida duplicación de posts antiguos verificando existencia en el DOM y en api_feed; se añadieron headers de seguridad y mejoras de accesibilidad. (PR feed-dup-accessibility-fix)
- Ajustado .fb-post y .fb-gallery para que la tarjeta crezca con imágenes múltiples (PR post-card-auto-height).
- Fixed trending.html variables to weekly_posts and top_notes to avoid UndefinedError (PR trending-variable-fix).
- Replaced moment.js filters with timesince/strftime and ensured CSRF macros in producto.html (PR moment-usage-removal).
- Comment modal moved to new component, comment.js created, fb-action-btn classes renamed and dark mode fixes for feed and store. JS errors cleaned (PR feed-store-comment-modal).
- Corregido el botón "Reclamar" de la racha diaria enlazando el evento en feed.js y actualizando los crolars con toast de confirmación (PR streak-claim-btn-fix).
- Eliminado modal de comentarios antiguo duplicado, quedando solo la versión con galería completa (PR comment-modal-cleanup).

- Visor de imágenes actualizado con panel lateral y zoom estilo Facebook (PR fb-photo-viewer).
- Comment modal now uses vertical gallery with fullscreen view on mobile (PR comment-modal-vertical)
- Fixed comments not loading in photo view by aligning markup and gallery lookup (PR comment-photo-view-fix)
- Photo view route now passes photo_index and loads comments dynamically via dataset (PR photo-view-comments-fix)
- /health endpoint now returns plain "ok" with status 200 and test updated (PR health-endpoint-plain).
- Photo view and API endpoints now allow anonymous access; comment form displays login prompt when not authenticated (PR photo-view-anon-fix).
- Removed duplicate image modal markup from base.html to ensure photo view loads post details correctly (PR photo-modal-duplicate-fix).
- Comment modal now reuses image_gallery macro for consistent gallery layout with feed (PR gallery-modal-unify).
- Navbar cleaned: removed Ranking link, backpack moved into personal space with new block. Launcher menu redesigned with grid of app icons. (PR grid-launcher-refresh)
- Launcher menu modernized with new component and CSS; floating options icon removed from profile via main.js (PR profile-launcher-redesign)
- Removed empty 'misiones' item from user dropdown and styled verified badge in purple (PR perfil-menu-badge-fix).
- Rediseñados logros en perfil público e interno con tarjetas responsivas, progreso y logros bloqueados; perfil_publico incluye perfil.css y feed.py usa import diferido de tasks (PR achievements-ui-fix).
- Módulo de logros renovado: tarjetas con tooltips, secciones de desbloqueados y bloqueados, botón 'Ver todos' y soporte responsivo/dark (PR achievements-redesign-modern).
- Public profile achievements now use modern cards with show-more and icons (PR achievements-public-profile-update).
- Added Word (.docx) and PowerPoint (.pptx) viewer for notes. Uses Mammoth.js for
  DOCX and converts PPTX to PDF with LibreOffice for inline display (PR notes-office-viewer).
- Notes upload now accepts DOCX and PPTX, storing original files and generating PDF previews. Added download of original PPTX (PR docx-pptx-upload).
- Added notes_count helper and updated templates to use it, preventing database errors when column missing (PR notes-count-helper).
- Nota detail ahora usa includes para visor según tipo de archivo y se guarda note.file_type en la base de datos (PR note-file-type-viewer).
- fly.toml now runs 'flask db upgrade' automatically so new columns like file_type are applied (QA fly-release-db-upgrade).
- Auto-creation del campo note.file_type si falta en la base de datos para evitar errores en /notes (QA note-file-type-hotfix).
- Vista previa de archivos en /notes/upload unificada: viewer.js maneja detección y muestra solo pdfPreview, docxPreview, imgPreview o pptPreview. Backend valida un único archivo por nota. (PR notes-upload-preview-fix)
- Toasts de la tienda ya no se muestran al cargar; main.js solo auto-muestra los que tienen data-autoshow (PR store-toast-trigger-fix).
- Feed now returns is_saved and user_reaction, keeping save button and reactions active on reload (PR feed-save-reaction-persist).
- Feed desktop now shows expandable '+' button with search, notifications and chat shortcuts (PR feed-desktop-fab)
- Floating '+' button now expands to the left showing quick notes, shortcuts and Crunebot (PR feed-fab-left-buttons)
- FAB buttons unified: quick notes, shortcuts and Crunebot merged into single floating menu; old buttons removed (PR feed-fab-unify)
- Corregido bloque extra_css en trending.html reemplazándolo por head_extra para que cargue estilos.
- Added prototype personal space with localStorage blocks and focus/dark modes (PR personal-space-proto).
- Banner superior eliminado en cursos para que la página inicie con "Mis Cursos Inscritos" (PR courses-banner-remove).
- Se corrigió la previsualización y subida de imágenes en el modal de publicaciones, limitando tamaño con CSS y enviando los archivos en feed.js (PR feed-upload-image-fix).
- Habilitado el blueprint personal_routes en /espacio-personal y enlace en menú de usuario (PR personal-space-enable).
- Restaurado diseño avanzado de espacio personal y eliminado blueprint personal_routes (PR personal-space-restore).
- Mejoradas funcionalidades del espacio personal: modo oscuro y enfoque persisten, sugerencias inteligentes ocultan tras usarse, y todos los bloques pueden crearse, editarse, eliminarse y reordenarse (PR personal-space-functional).

- Focus mode now persists using localStorage and starting the personal space creates Nota, Kanban and Objetivo blocks. Added aria-labels for accessibility. (PR personal-space-persistence)
- Theme color meta tag updates with dark mode and various buttons have aria-labels and titles for accessibility. (PR personal-space-ui-fixes)
- Added Block model, migration and /api/create-block endpoint with JS integration for suggestions (PR personal-space-db-blocks).
- Personal space now loads blocks from the new Block model, rendering them dynamically with drag & drop and suggestions creating database records. (PR personal-space-blocks-ui)
- Fully activated personal space blocks using the database: JS calls /api/create-block, block cards use data-block-type, PersonalBlock routes replaced with Block and helper for overdue items. (PR personal-space-full-fix)
- Fixed personal space buttons: script loads via extra_js, listeners added for #createFirstBlock and smart suggestions using handleSuggestionAction. (PR personal-space-buttons-fix)
- Unified personal space initialization: removed DOMContentLoaded handlers, exported initPersonalSpace and called from main.js; empty-state button now calls startPersonalSpace. (PR personal-space-init-fix)
- Renamed getCSRFToken calls to getCsrfToken to avoid JS errors in personal-space.js (PR personal-space-csrf-func-fix).
- Personal space layout refreshed with compact cards, top metrics and disappearing suggestions. startPersonalSpace waits for API responses (PR personal-space-ui-refresh).
- Added SortableJS script via extra_js block to ensure drag-and-drop works (PR personal-space-sortablejs-fix).
- Block model regained progress calculation and overdue check to prevent template errors (PR block-methods-fix).
- Corregido visor de fotos: las flechas actualizan la imagen usando #modalImage y el panel lateral evita overflow con comentarios scrollables (PR photo-modal-navigation-fix).
- Added generic block viewer with placeholder page and Kanban view; cards now feature an 'Entrar' button and double-click navigation (PR personal-space-access-improvements).
- Upload form now uses Tom Select with expanded categories and academic levels (PR notes-category-select).
- Added IA_ENABLED config flag, disabled OpenAI calls when off and provided static quick responses with status badge (PR crunebot-fake-mode).
- Previsualización de imágenes en el chat, corrección de mensajes privados y diseño más compacto (PR chat-image-preview).
- Eliminada votación y reacciones al borrar apuntes y publicaciones para evitar violación de claves foráneas (PR fix-cascade-delete).
- Eliminación de apuntes y posts ahora borra votos/reacciones asociados y maneja IntegrityError para evitar fallos (PR delete-related-cleanup).
- Corregido scroll infinito del feed: nueva ruta /feed/load con paginación, loader con mensajes y JS que evita peticiones duplicadas (PR feed-scroll-fix).
- Posts cargados via scroll ya no desaparecen y se eliminó el texto "Cargando más..." dejando solo el spinner (PR feed-loader-text-remove).
- Añadidos logs de depuración en loadFilteredFeed y loadMorePosts y condición para no limpiar el feed al recargar con el mismo filtro (PR feed-scroll-disappearing-fix).
- Ajustado loadFilteredFeed para respetar currentPage>1, proteger innerHTML y registrar actualización; loadMorePosts incluye timeout de seguridad y /feed/load muestra mensaje cuando no hay más publicaciones (PR feed-scroll-empty-fix).
- Añadidos console logs en loadMorePosts para depurar HTML y elementos, se inserta cuando falta data-post-id y se muestra mensaje cuando no hay más publicaciones (PR feed-scroll-debug-fix).
- Marketplace filters toggle: sidebar oculto por defecto y categorías completas en modal con Tom Select (PR store-filters-toggle)
- Fixed store routes to pass STORE_CATEGORIES dictionary and removed duplicate precio_min logic to avoid Jinja errors (PR store-categories-dict).
- Fixed publish product modal using category groups via categories_dict (QA store-category-dict-fix).
- Fixed Filters button in /store: sidebar toggles correctly with rotating icon and mobile IDs renamed to avoid duplicates (PR store-filters-btn-fix).
- Mobile navbar: removed 'Carrera', moved 'Perfil' to the rightmost slot and added accessibility/headers fixes (PR mobile-nav-carrera-remove).
- Enlaces a Liga, Desafíos y Mi Carrera ocultos para usuarios normales y rutas redirigen al feed si el rol no es admin (PR restrict-incomplete-pages).
- Vista /notes redise\u00f1ada como galer\u00eda A4: alias /apuntes, tarjetas verticales con t\u00edtulo arriba, sidebar removido y responsive (PR notes-a4-gallery).
- Fixed account deletion by removing related records, added confirmation and flash message (PR delete-account-fix).
- Tarjetas de apuntes modernizadas con sección de autor, etiquetas y menú de opciones; incluyen skeleton de carga y métricas inferiores (PR note-card-redesign).
- Indicadores de verificación rediseñados: se quitan badges verdes, icono junto al nombre y efecto glow en tarjetas (PR notes-verified-ui).
- Generado filtro `cl_url` y helper optimize_url para insertar `f_auto`, `q_auto` y tamaños al construir URLs de Cloudinary; se actualizaron avatares, galerías y tienda (PR cloudinary-optimizations).
- Fixed comment null errors and share modal duplicates, styled inactive feed buttons, improved note-card layout with flexbox and added optimistic save (PR feed-bugfixes-ui).
- Scoped comment event delegation to #feedContainer to avoid modal conflicts (PR comment-events-scope).
- Fixed comment rendering in gallery modal: API now returns avatar and JS uses valid selector for modal inputs (PR gallery-modal-comment-fix).
- Filtro "Apuntes" en /feed muestra tarjetas en cuadrícula añadiendo la clase
  `feed-as-grid` y estilos grid en CSS (PR feed-notes-grid).
- notes.css ahora se carga globalmente desde base.html para mantener el diseño
  de note-card consistente en el feed (PR feed-note-card-css).
- Estilos de note-card unificados en notes.css y eliminados de carrera.css; selectores fortalecidos con prefijo .note-card. (PR note-card-centralize)
- Vistas previas de notas ahora se inicializan con `initNotePreviews`, llamado tras cargar contenido dinámico en el feed y otras páginas. (PR note-preview-reinit)
- Toggle filters sidebar via filter-toggle-btn and CSS transform (PR marketplace-filters-fix).
- Marketplace sidebar now fixed-position with overlay; button toggles body class for smooth slide (PR marketplace-sidebar-bugfix).
- Refactored post modal layout with fixed header and footer so comment input stays visible and comments scroll separately (PR post-modal-layout-fix).
- Updated fly.toml with http_service health check grace period and performance VM to avoid startup 503 errors (PR fly-health-vm).
- Reverted Gunicorn to synchronous worker for reliable startup (PR gunicorn-sync-worker).
- Simplified fly.toml and Dockerfile to use a single gunicorn command with 3 workers and no services block (PR fly-config-cleanup).
- os.makedirs("instance") now uses exist_ok=True to avoid startup error (PR db-instance-exist-ok).
- min_machines_running set to 1 in fly.toml to keep one machine running (PR fly-autostop-fix).
- Added dedicated /healthz endpoint returning 'ok' and updated fly.toml health check path (PR healthz-endpoint).
- Modernized notes list with purple filter buttons, Bootstrap icons and DOMContentLoaded wrappers for initNotePreviews (PR notes-ui-refresh).
- Improved healthz endpoint to validate DB connection and increased timeout to 15s (PR health-check-db-timeout).
- Ajustados estilos de filtros y barra de búsqueda en /notes para respetar la paleta morada y mejorar el contraste (PR notes-filters-css-refactor).
- Lightweight wsgi health check via Dispatcher; removed DB access from health blueprint (PR wsgi-light-health).
- Reacciones y modales actualizados con panel flotante y long press; feed.js maneja hover y textos personalizados (PR reactions-refactor).
- Función de compartir restaurada con navigator.share y copia como respaldo; botón único sin extras (PR share-native-restore).
- Reverted to eventlet Gunicorn worker to fix 'Bad file descriptor' socket errors (PR gunicorn-eventlet-fix).
- Adopted Option 2: eventlet worker with healthz and min_machines_running improvements (PR eventlet-option2)
- Removed dynamic share option overlay and related CSS; share buttons now use built-in navigator.share only (PR share-options-remove).
- Fase 2: reconstruido botón Me Gusta con conteo estable, handleLike actualiza solo el contador y color activo igual a Guardar.
- Fase 3: panel de reacciones con long press flotante, scroll horizontal y contador clickeable.
- Added csrf macro import in store/_product_cards.html to fix UndefinedError in search_products (hotfix product-cards-csrf).
- Fixed note upload failing with invalid integer when "reading_time" empty; route now parses it to int when provided (PR notes-reading-time-int).
- Fixed notes filter buttons active color to white via .notes-filters .btn-outline-primary.active rule (PR notes-filters-contrast-fix).
- Fixed like button icon disappearing; consistent structure with count in post card and modals, safe JS updates and global search check (PR like-button-fix).
- Restored fire icon in like buttons and guarded legacy search click handler (PR like-icon-restore)
- Consolidated DOMContentLoaded handlers from comment.js, forum_editor.js, enhanced-ui.js, store.js, league.js and feed.js into main.js; modules expose init functions (PR domcontent-modules-consolidation).
- Guarded reaction button initialization to prevent TypeError on pages without .btn-reaction (PR feed-reaction-null-check).
- Feed routes split into subpackage crunevo/routes/feed with views.py and api.py; feed_routes.py now re-exports for compatibility (PR feed-subpackage).
- Guarded streak claim button event listener to prevent errors when element is missing (PR feed-missing-element-guard).
- Guarded reaction button initialization to prevent TypeError on pages without .btn-reaction (PR feed-reaction-null-check).
- Created api package with JWT-authenticated endpoints and updated README with usage instructions (PR feed-api-blueprint).
- frontend directory contains a decoupled Next.js SPA built with Tailwind.
- FeedPage under `frontend/app/feed/page.tsx` consumes `/api/feed` using `fetch`.
- Build the SPA separately with `docker build -t crunevo-frontend -f frontend/Dockerfile frontend`.
- Deploy frontend and backend containers independently; the SPA communicates with the Flask API via HTTP.
- Session cookies default to `SESSION_COOKIE_SECURE=True` and `SESSION_COOKIE_SAMESITE='Lax'` in `config.py`. Production sets `SESSION_COOKIE_HTTPONLY=true` in `fly.toml` and `fly-admin.toml` (PR session-cookie-security).
- Enabled Dependabot weekly updates for pip packages and added CI workflow running 'make test' on PRs (PR dependabot-ci).
- CI workflow runs 'make fmt' and 'make test' on every push (PR workflow-fmt-test).
- SECRET_KEY now required from environment; config warns in debug and errors in
  production (PR secret-key-env).
- Split auth.login and feed.view_feed logic into new services for authentication and feed data retrieval (PR login-feed-services).
- Added paginated comments API and load-more button in modals; feed.js handles fetching additional pages (PR comments-pagination).
- Comment modal logic consolidated into feed.js; comment.js reduced to a stub and main.js initializes the unified code (PR comment-module-unify).
- Added reactions list modal with /feed/api/reactions/<post_id> endpoint and JS handler (PR reactions-list-modal).
- Comment and photo modals now include ARIA labelling and keyboard focus for improved accessibility (PR modals-aria-accessibility).
- Comment submission now inspects fetch errors and shows friendly messages; buttons re-enable on failure (PR comment-error-messages).
- Replaced manual CSRF inputs with `csrf_field()` and imported csrf macro in comment and post modals (PR csrf-template-fix).
- Release command sets random SECRET_KEY to avoid missing env error (PR release-secret-fix).
- Added comment deletion endpoint `/feed/comment/delete/<id>` with author/moderator authorization (PR comment-delete-endpoint).
- Consolidated openCommentsModal, submitModalComment and addCommentToModalUI into comment.js; feed.js references them and main.js calls initCommentModals once (PR comment-modal-refactor).
- Defined .bi-fire-fill in fix-bootstrap.css to keep the fire icon visible when liking posts (PR like-fire-icon-fix)
- Perfil público ahora reutiliza el banner y el formulario de publicaciones; enlaces de perfil en navbar, sidebar y navegación móvil usan profile_by_username (PR public-profile-banner-modal).
- Replaced "Editar perfil" button with "Detalles personales" fixed inside the profile header and ensured achievements section spacing and mobile grid (PR profile-details-btn).
- Reemplazado botón "Editar perfil" por "Detalles personales" solo visible en el perfil propio; ajustada redirección a /perfil en lugar de configuración (PR perfil-detalles-fix).
- Fixed Jinja if/else in perfil_publico.html to avoid TemplateSyntaxError and show actions for other users (hotfix perfil-conditional-fix).
- Se implementó sistema de errores para admins en /admin/errores. Captura automática, vista filtrable y botón de resolución.
- Detecta 'no-more-posts' en feed.js para detener el infinite scroll y ocultar el loader (PR feed-load-end).
- loadFilteredFeed muestra mensaje si data.html está vacío sin limpiar el contenedor y reinicia reachedEnd/currentPage (hotfix quickfeed-empty)
- loadMorePosts y loadFilteredFeed ahora ocultan el loader y muestran un alert si ocurre un error; registran el status HTTP y respuesta para depuración (PR feed-error-handling).
- Removed unused global comment modal in feed.html; each post modal now uniquely references commentsModal-<post.id> (PR comment-modal-id-cleanup).
- Improved notifications dropdown reload: shows error toast when request fails, keeps previous entries when empty with message 'No hay notificaciones nuevas' and refreshes only if tab visible (PR notifications-error-toast).
- Updated notifications.js to query #notificationsDropdown and #notifications-list; replaced .notification-container selector (PR notifications-dropdown-selector).
- Removed legacy initNotifications from main.js; dropdown updates now rely on initNotificationManager (PR remove-initNotifications).
- loadFilteredFeed ahora verifica response.ok, registra errores y conserva el contenido previo en caso de fallo; solo actualiza el contenedor cuando data.html no está vacío (hotfix feed-filter-ok-check).
- removeSkeletonPosts ahora registra los skeleton eliminados; loadFilteredFeed y loadMorePosts muestran el HTML recibido y solo limpian el contenedor si cambia el filtro. notifications.js registra conteos y si el dropdown se actualiza o se conserva (PR feed-notif-logging).
- removeSkeletonPosts and deletePost now log the selectors of elements before applying fade-out or removal. Actual posts use the 'facebook-post' class; '.post-skeleton' is only for loading placeholders.
- Verified post_card.html renders articles with class 'facebook-post' only; no 'post-skeleton' or 'fade-out' classes found in templates or server logic.
- Searched repo for any rules hiding '.facebook-post' elements; none found beyond normal styles. Confirmed removeSkeletonPosts() only selects '.post-skeleton'. Documented findings for future reference.
- Added diagnostic CSS borders for `.facebook-post` at end of feed.css to visualize opacity and fade-out behaviors during testing.
- Inserted diagnostic borders after `.facebook-post` styles in feed.css to debug hidden posts.
- toggleComments now logs the element being hidden before applying the `fade-out` class and showToast logs the toast element before fade-out for easier debugging.

- Added raw HTML logs in feed.js for debugging rendered posts.
- Added temporary CSS borders for `.facebook-post` diagnostics.
- Added console logs when applying `fade-out` to track element removal.
- Removed debugging borders and logs from feed.js; fade-in/out animations now use
  `forwards` fill mode and loader hides after successful load to fix invisible
  posts issue.
- Updated reaction panel with floating overlay and modern emojis; adjusted templates and JS.
- Restored CRUNEVO emojis in floating reaction panel; kept overlay JS improvements (PR modern-floating-reactions-fix).
- Enhanced floating reaction panel design with fade animations, hover bounce and higher z-index; updated CSS, JS and templates (PR reactions-panel-style-improve).
- Updated reactions macro to use like-btn markup, added blur backdrop and prevented default on long press to fix overlay bug (PR reaction-panel-bugfix).
- Ensured floating reaction panel is visible by removing overflow restriction on `.facebook-post` (PR fix-reaction-panel-not-showing-v2).
- ModernFeedManager initializes when any .like-btn is present to restore floating reactions on post detail pages (hotfix floating-reactions-init).
- Fix position and style of floating reaction panel above "Me gusta" button (PR reactions-panel-position-fix).
- Fixed reaction panel placement by measuring after display; removed horizontal scrollbar and wrapped buttons; panel now positions reliably above the like button (PR reaction-panel-enhancements).
- Unified reaction panel logic in main.js and feed.js with dynamic positioning, simplified CSS and templates (PR reaction-panel-unify-fix).
- Corrected floating reaction panel to appear centered above the pressed "Me gusta" button and reset styles on hide (PR reaction-panel-button-align).
- Improved mobile reaction panel positioning to center over the tapped like button with screen margins and click-outside close handler (PR mobile-reaction-panel).
- Restored repository to pre-replit state and removed stray metrics migration to fix Alembic heads (hotfix revert-replit)
- Restored Fly volume mount in fly.toml to match existing machine configuration (PR fix-fly-volume-config)
- Confirmed Next.js SPA under `frontend/` remains as the official frontend. Documented build and deployment instructions in README (QA spa-integration-doc).
- Cleaned unnecessary console.log statements in static JS and guarded service worker logs with self.DEBUG (PR remove-console-logs).
- Added audit logging in require_admin before_request to track admin page visits (PR admin-require-logging).
- Added /admin/api/analytics endpoint and improved applyFilters to send selected filters and redraw charts (PR analytics-filters-api).
- Replaced debug `console.log` statements in base.html and ranking/index.html with `console.info` for clearer logging (PR template-console-cleanup).
- Replaced mobile bottom nav with a translucent top mobile navbar on small screens, kept hamburger menu intact and removed obsolete component includes (PR facebook-mobile-navbar).
- Redesigned mobile navbar with purple translucent background, circular icon buttons and updated order (Inicio, Personas, Chat, Apuntes, Notificaciones, Tienda), removing the perfil link (PR mobile-navbar-facebook-style).
- Ajustado navbar móvil para fondo morado sólido, altura mínima 64px y sombra sutil; modal de búsqueda visible en móviles (PR mobile-navbar-fix).
- Trending page now lists top posts, notes and popular forum questions with a link to ranking. Added Tailwind classes for modern layout (PR trending-forum-ranking).
- Rediseño completo de la página Trending con layout moderno y atractivo: hero section con estadísticas, cards mejoradas con rankings, badges de estado, efectos hover, diseño responsive optimizado y mejor UX (PR trending-complete-redesign).
- Trending page accessible without login; trending route no longer requires activation and handles guests. (hotfix trending-public)
- Trending route now skips forum query when forum tables missing and logs exception (hotfix trending-forum-missing-table).


## Rediseño completo del foro como "Centro de Matemáticas" (Diciembre 2024)

Se realizó una mejora integral del foro transformándolo en un "Centro de Matemáticas" con temática educativa y elementos visuales atractivos:

### Cambios realizados:

**CSS y estilos (`crunevo/static/css/forum_editor.css`):**
- Agregados estilos matemáticos con variables CSS para colores temáticos
- Implementadas animaciones y transiciones suaves
- Creados efectos hover y gradientes matemáticos
- Soporte para modo oscuro y responsive design
- Estilos especiales para badges de categorías con colores específicos

**Página principal del foro (`crunevo/templates/forum/list.html`):**
- Transformado el título a "Centro de Matemáticas" con header animado
- Agregados iconos matemáticos (🧮, ∑, π, ∞, ∆, ∫) 
- Implementados filtros de categoría mejorados con iconos específicos
- Creadas cards de preguntas con efectos hover y bordes decorativos
- Sidebar mejorado con estadísticas, consejos matemáticos y herramientas
- Panel de insights matemáticos contextual

**Vista de pregunta individual (`crunevo/templates/forum/question.html`):**
- Rediseño completo con breadcrumbs matemáticos
- Header de pregunta mejorado con mejor información del autor
- Separador matemático decorativo (∞)
- Botones de ordenamiento para respuestas múltiples
- Formulario de respuesta mejorado con consejos
- Sidebar expandido con herramientas matemáticas y quote inspiracional

**Formulario para hacer preguntas (`crunevo/templates/forum/ask.html`):**
- Interfaz completamente rediseñada con progreso visual
- Pasos numerados para guiar al usuario
- Tips matemáticos interactivos y consejos de calidad
- Vista previa y validación en tiempo real
- Header matemático inspiracional con emojis
- Mensajes de aliento y símbolos matemáticos

**Componente de respuestas (`crunevo/templates/forum/partials/answer_card.html`):**
- Diseño mejorado con avatares destacados
- Badges informativos para colaboradores
- Botones de voto rediseñados con efectos
- Mensaje especial para respuestas aceptadas
- Mejor organización visual y espaciado

**Navegación:**
- Actualizado enlaces en navbar (`crunevo/templates/components/navbar.html`)
- Modificado sidebar izquierdo (`crunevo/templates/components/sidebar_left_feed.html`)
- Cambiado de "Foro" a "Centro Matemático" con icono de calculadora

### Características destacadas:
- Temática matemática coherente en toda la interfaz
- Iconos específicos para cada categoría académica
- Animaciones CSS suaves y efectos de hover
- Diseño responsive optimizado para móviles
- Elementos de gamificación (progreso, badges, puntos)
- Herramientas matemáticas integradas (Desmos, GeoGebra, Wolfram Alpha)
- Mensajes motivacionales y tips educativos
- Soporte completo para modo oscuro

Todos los cambios mantienen la funcionalidad original mientras mejoran significativamente la experiencia visual y educativa del foro.

- Reverted forum to general "Foro Estudiantil", removing math-only branding. Updated navbar, sidebar, templates and CSS variables. (PR forum-general-qa)

- Modernized Club system with comprehensive feature enhancements including banner/avatar uploads, social media integration, creator permissions and modern UI design. Added banner_url, facebook_url, whatsapp_url and creator_id fields to Club model with proper relationships. Enhanced ClubForm with file upload fields and URL validation. Updated create_club route with Cloudinary integration for image uploads and proper creator assignment. Added edit_club functionality restricted to creators and admins. Implemented banner display with gradient overlays, social link buttons, and creator information in detail view. Enhanced list view with banner previews and social media indicators. Applied modern styling with smooth animations, hover effects and responsive design. All forms follow CSRF protection and established styling guidelines.
- Fixed missing Alembic dependency by pointing `club_modernization_fields` to `new_sections_2024` and created merge revision `f516460c56d7` to unify heads with `add_system_error_log`. (PR fix-migrations-heads)
- Verified feed management features in admin routes and templates, confirming post deletion and comment moderation. (QA feed-admin-functions-check)
- Added notes management page in admin with CSV export and deletion options (PR admin-notes-management).

- **Major Forum Modernization with Brainly-like Features (2024-01-XX)**: Completely redesigned the student forum to be better than Brainly with comprehensive enhancements across all aspects:

  **Backend Enhancements:**
  - Extended ForumQuestion model with difficulty_level, subject_area, grade_level, bounty_points, is_urgent, is_featured, quality_score, homework_deadline, exam_date, context_type fields
  - Extended ForumAnswer model with explanation_quality, has_step_by_step, has_visual_aids, is_expert_verified, confidence_level, helpful_count, word_count, estimated_reading_time, contains_formulas, contains_code fields
  - Added ForumTag model with many-to-many relationship to questions for better categorization
  - Added ForumReport model for community moderation and content reporting
  - Added ForumBadge model for gamification with user achievements system
  - Created association tables for user bookmarks, answer votes, and user badges
  - Enhanced forum routes with advanced filtering, sorting, search, tags system, and bounty management
  - Added bookmark functionality, improved voting system with vote tracking, and expert verification
  - Implemented comprehensive search with multi-criteria filtering and tag support
  - Added automatic answer quality detection and content analysis

  **Visual Design Overhaul:**
  - Removed old forum header and "Did you know" banner elements as requested
  - Completely redesigned list.html with modern, mobile-first, minimal interface
  - Implemented card-based layout with clean typography and responsive design
  - Added advanced filters panel with collapsible interface and real-time updates
  - Created modern search interface with live statistics and quick action buttons
  - Designed comprehensive tag system with color-coded categories and auto-complete
  - Added difficulty level badges, urgency indicators, and bounty system visualization
  - Implemented modern pagination with improved navigation

  **Enhanced Ask Question Experience:**
  - Redesigned ask.html as a 4-step wizard with progress tracking
  - Added title character counter and real-time validation
  - Implemented comprehensive categorization with difficulty levels and grade levels
  - Added context selection (homework, exam, curiosity, project)
  - Created modern tag input system with suggestions and auto-complete
  - Added advanced options including urgency flags and deadline setting
  - Implemented bounty system where users can offer points for better answers
  - Added sidebar with tips, examples, and community statistics
  - Created step-by-step navigation with completion validation

  **Search & Discovery:**
  - Created search_results.html template for advanced search results
  - Added search statistics dashboard with result metrics
  - Implemented applied filters display with easy removal options
  - Added comprehensive result cards with all question metadata
  - Created tag-based navigation and filtering system

  **Mobile Optimization:**
  - Designed fully responsive interface optimized for mobile devices
  - Implemented touch-friendly controls and swipe gestures
  - Added collapsible sections and optimized spacing for small screens
  - Created adaptive layouts that work seamlessly across all device sizes

  **Quality & Features:**
  - Added automatic answer quality scoring based on multiple factors
  - Implemented step-by-step detection and visual aids recognition
  - Added expert verification system for high-quality answers
  - Created helpful votes separate from regular voting
  - Added automatic word count and reading time estimation
  - Implemented formula and code detection in answers

  **User Experience:**
  - Added bookmark system for saving interesting questions
  - Implemented share functionality with native mobile sharing
  - Created live progress tracking in question creation
  - Added real-time character counters and validation feedback
  - Implemented auto-save and form persistence
  - Added comprehensive error handling and user feedback

  This modernization transforms the forum into a comprehensive learning platform that rivals and exceeds Brainly's functionality while maintaining a clean, minimal design optimized for both desktop and mobile use.
- Added migration 'add_forum_modernization_fields' to create missing tables and columns for the modern forum.
- Handled missing forum tables gracefully in list_questions to avoid 500 errors (PR forum-500-fix).
- Added migration 'forum_modernization_schema' and removed temporary error handling from forum routes.
- Fixed popular sort in forum by counting answers via join instead of property (hotfix forum-popular-sort).
- Improved forum list route with robust DB error handling and orphan author fallbacks (PR forum-list-stability).
- Added ensure_forum_tables helper and manual 500 error for missing schema; created test for /foro (PR forum-table-check).
- Fixed description validation on /foro/hacer-pregunta with char counter, drag-drop images and backend length check (PR forum-editor-enhancements).
- Removed duplicate Quill initialization on /foro/hacer-pregunta, ensuring single editor with image uploads and accurate character counter (PR forum-editor-single).
- Improved /foro/hacer-pregunta editor with precise whitespace-trimmed character validation, richer Quill toolbar, resizable images with tooltip and click-to-expand, and enforcement of 20-character minimum before advancing (PR forum-editor-validation-fix).
- Fixed character counter on /foro/hacer-pregunta using Quill text content and ignoring punctuation, enabling 20-character validation without errors (PR forum-editor-charcount-bugfix).
- Ensured /foro/hacer-pregunta editor enables "Siguiente" after 20 real characters by waiting for Quill initialization and using robust content validation (PR forum-editor-next-btn-fix).
- Fixed modal navigation by managing history state with a stack and popstate listener, preventing unintended page back navigation when closing new Facebook-style modals (PR modal-history-fix).
- Unified Facebook-style post modal: added color variables, refactored feed.js with createModal/closeModal helpers, and trimmed _post_modal.html to panel-only content (PR facebook-modal-refactor).
- Full-screen Facebook-style modal restored zoom, navigation, download and options controls with scroll-safe info panel (PR facebook-modal-controls).
- Introduced dual modal system: full-screen photo modal with advanced controls and restored Bootstrap comment modal, removing comments-only styles and logic (PR dual-modal-system).
- Unified comment input across photo and comment modals with fixed bottom form and reusable CSS for Facebook-like design (PR unified-comment-input).
- Made photo modal responsive for mobile, added unique IDs per post and ARIA-labelled controls to address accessibility warnings (PR photo-modal-mobile-fix).
- Fixed comment modal layout with flexbox to keep header and input fixed and added compact comment form styles reused in photo modal for consistency (PR comment-modal-compact-form).
- Removed Bootstrap's extra scroll class from comment modal to ensure a single scroll area and matched photo modal comment form width using w-100 (PR comment-modal-single-scroll).
- Refactored comment and photo modals into single-page scrollable layouts, locked body scrolling and anchored comment input at bottom for consistency (PR modal-unified-scroll).
- Ensured modals remain within viewport using 90vh content height, moved all scroll to internal containers and kept comment input fixed to eliminate outer scrollbars (PR modal-scroll-layout-fix).
- Implemented single-scroll comment modal with compact comment CSS, load-more button fetching paginated comments with has_more flag, and updated tests to cover new API (PR comment-modal-infinite-scroll).
- Removed nested scroll by stripping overflow and height limits from `.modal-comments-section`, consolidating scrolling to the parent container (PR modal-comments-scroll-fix).
- Rebuilt post and comment modals with two-panel layout, fixed header and bottom comment form, and single scrollable info panel with responsive stacking (PR modal-two-panel-layout).
- Resolved double scroll in Facebook-style modal by enforcing flexbox layout with a single scrollable content area, updating comment modal markup and scroll handling (PR modal-single-scroll-fix).
- Eliminated remaining double scroll in comment modal by moving the comment form inside a single scrollable body, making it sticky at the bottom and removing inner comment list overflow (PR comment-modal-sticky-input).
- Consolidated comment modal layout by placing the comment form outside the scrollable body, cleaning duplicate comment styles and reinforcing single-scroll behavior with sticky input (PR comment-modal-css-cleanup).
- Centered comment modal horizontally on desktop, added responsive full-width behavior on mobile, and preserved sticky comment form (PR comment-modal-center).
- Optimized comment modal input with full-width auto-expanding textarea and minimal send button for better mobile usability (PR comment-input-opt).
- Fixed navbar macros: consolidated user auth conditional and guarded current_user usage to resolve TemplateSyntaxError and test failures (PR navbar-auth-conditional).
- Migrated mobile "NotBar" component to "MobileNavbar", renamed template and CSS class `.notbar` to `.mobile-navbar` and updated includes (PR mobile-navbar-rename).
- Documented mobile navigation bar usage and noted replacement of bottom nav (PR mobile-navbar-docs).
- Refined mobile navbar: new purple blur style with circular buttons, forum icon now question mark, and search input opens a full-screen modal with live suggestions (PR mobile-navbar-enhance).
- Mobile navbar badges and spacing fixed: icons spaced evenly, notification button links to full page with working badge, cart count now visible, and auto-hide/padding logic targets the mobile navbar (PR mobile-navbar-fixes).
- Calculated navbar height dynamically with CSS variable, updated sidebar offset and scroll padding, and unified auto-hide logic to ensure content isn't covered on any page (PR navbar-overlap-fix).
- Reapplied navbar height on load and resize, setting body padding and scroll offset to prevent content being hidden by fixed navbars (PR navbar-padding-load).
- Recalculated navbar height on DOMContentLoaded and window load to prevent fixed navbar from covering content on mobile and desktop (PR navbar-height-recalc).
- Fixed indentation of marketplace and related blueprint imports in `app.py` to resolve deployment error (hotfix marketplace-import-indent).
- Added missing marketplace utilities and models overhaul: created `utils/uploads` helper, simplified marketplace models, fixed conversation/message relations, updated routes and templates, and ensured CSRF tokens in forms (PR marketplace-fixes).
- Added migration to create marketplace tables and product fields and rolled back DB session before logging errors to avoid aborted transactions (PR marketplace-subcategory-fix).
- Fixed seller registration page 500 error by importing csrf macro and sanitized marketplace price filters to avoid "None" in numeric inputs (hotfix marketplace-become-seller).
- Handled `None` values in marketplace filter inputs to prevent invalid numeric field values (hotfix marketplace-filter-none).
- Fixed seller dashboard 500 by providing required context variables and timestamp alias for messages (hotfix seller-dashboard-context).
- Guarded seller dashboard template against missing product or sender references to prevent runtime errors (hotfix seller-dashboard-template-guards).
- Added `is_official` field to `Product` model with default `False` and migration to support official products (PR add-product-is_official).
- Restricted store index and related product queries to `is_official=True` so only official products appear (PR store-official-filter).
- Marketplace now displays a badge for official products and includes them alongside seller listings (PR marketplace-official-badge).
- Unified `Product` model across store and marketplace: removed duplicate favorite/purchase queries and enforced `is_official` filter in views `store.store_index`, `store.view_product`, `store.redeem_product`, `store.buy_product`, `store.add_to_cart`, `store.view_cart`, `store.checkout`, `store.toggle_favorite` and `marketplace.marketplace_index`.
- Added unified product route `/producto/<id>` with conditional template and redirects from legacy store and marketplace paths (PR product-view-unify).
- Added error handling and missing context for marketplace seller and message views to prevent 500 errors (hotfix marketplace-route-errors).
- Registered `timeago` and `date` template filters and imported CSRF macro in marketplace templates to prevent undefined filter errors and ensure proper form protection (hotfix marketplace-filters-csrf).
- Implemented pagination in seller_products view, passing pagination context and guarding template to avoid undefined errors (hotfix seller-products-pagination).
- Fixed marketplace messages link to use `marketplace.marketplace_index` and guarded optional image upload routes to avoid BuildError (hotfix marketplace-messages-link).
- Marketplace product detail view now renders `marketplace/view_product.html` with seller info, related products and CSRF macro (PR marketplace-product-detail-template).
- Fixed seller product editing by including unread message count in edit view and replaced delete links with POST forms and CSRF to enable product removal from seller panel (hotfix seller-product-actions).

## Store and Marketplace Unification

- Unified Store and Marketplace modules into a single Commerce module with shared templates and routes.

## Feed Interactions Improvement

- Mejorado el sistema de interacción con publicaciones en el feed:
  - Implementada funcionalidad para abrir el modal de comentarios al hacer clic en el contador de comentarios.
  - Añadida sincronización de datos en tiempo real para el modal de comentarios mediante API.
  - Creado endpoint `/feed/api/comments/<post_id>` para obtener comentarios actualizados.
  - Mejorada la accesibilidad de los modales con atributos ARIA adecuados.
  - Expandido el menú de opciones de publicaciones (tres puntos) con nuevas funcionalidades:
    - Copiar enlace de la publicación
    - Guardar publicación
    - Reportar publicación (existente)
  - Implementados controladores JavaScript para las nuevas opciones del menú.
  - Añadida función `copyToClipboard` con soporte para API moderna y fallback para navegadores antiguos.
  - Mejorada la experiencia de usuario con retroalimentación visual y notificaciones toast.

## Sidebar Optimization

- Optimizado el sidebar derecho del feed para mejorar la experiencia de usuario:
  - Rediseñada la sección de tendencias para mostrar publicaciones reales con sus estadísticas.
  - Mejorada la sección de contribuidores destacados para mostrar usuarios reales con sus puntos semanales.
  - Implementada la sección de logros recientes con datos dinámicos de la base de datos.
  - Añadido sistema de tips de estudio aleatorios para mayor variedad de contenido.
  - Reorganizada la sección de enlaces útiles con mejor distribución espacial.
  - Mejorada la estética general con efectos hover, transiciones suaves y mejor espaciado.
  - Implementada responsividad para dispositivos móviles.
  - Añadidos enlaces "Ver más" en cada sección para facilitar la navegación.
- Created new template `tienda/_product_cards.html` for displaying product cards with dynamic rendering of product information including images, names, descriptions, badges, ratings, prices, and action buttons.
- Created unified template `tienda/producto.html` for displaying detailed product information with breadcrumb navigation, image carousel, product details, action buttons, description, shipping information, and tabs for reviews and questions.
- Created template `tienda/carrito.html` for the shopping cart with product details, quantity controls, and order summary.
- Updated `app.py` to register the new unified commerce blueprint and removed the old store and marketplace blueprints.
- Added legacy redirects in `commerce_routes.py` for specific routes from the old store and marketplace modules to the new unified commerce module.
- Created template `tienda/checkout_confirm.html` for the checkout confirmation page with order summary and shipping options.
- Created template `tienda/checkout_success.html` for the checkout success page with order details and purchased products.
- Created template `tienda/compras.html` for displaying a user's purchases with search, sorting, and review options.
- Created template `tienda/favorites.html` for displaying a user's favorite products with search, sorting, and cart actions.
- Created template `tienda/request_product.html` for product requests with form and previous requests display.
- Created template `tienda/my_requests.html` for displaying a user's product requests with search, filtering, and detailed information.
- Created template `tienda/become_seller.html` for the "Become a Seller" page with benefits, guide, and registration form.
- Created comprehensive template `tienda/seller_dashboard.html` for the seller dashboard with navigation sidebar and sections for dashboard statistics, products, orders, messages, reviews, and settings.

## Sistema de Eventos y Panel Administrativo

- Implementado sistema completo de gestión de eventos con las siguientes características:
  - Extendidas las rutas en `event_routes.py` para incluir todas las funciones necesarias:
    - `crear_evento()` (existente, mejorado)
    - `editar_evento(event_id)` (nuevo)
    - `eliminar_evento(event_id)` (nuevo)
    - `ver_evento(event_id)` (existente)
    - `listar_eventos()` (existente)
    - `mark_attendance()` (nuevo) para marcar asistencia y otorgar créditos
  - Aplicados decoradores de permisos adecuados (`@admin_required`, `@login_required`) a todas las rutas
  - Integrado el sistema de eventos con el panel administrativo mediante `admin_routes.py`
  - Creadas plantillas administrativas:
    - `admin_event_list.html`: Lista de eventos con filtros, búsqueda y exportación CSV
    - `admin_event_form.html`: Formulario para crear y editar eventos
    - `admin_event_detail.html`: Detalles del evento y gestión de participantes
  - Integración con el sistema de créditos para recompensar la asistencia a eventos
  - Soporte para eventos destacados, próximos y pasados con filtros
  - Categorización de eventos (taller, seminario, feria, conferencia, etc.)
  - Acceso a eventos desde el menú de navegación del panel administrativo
- Created template `tienda/publish_product.html` for publishing or editing products with form fields and image upload.
- Replaced `auth.profile_by_username` links with `auth.view_profile` across templates to resolve navbar BuildError (hotfix profile-link).

- Added legacy blueprints to redirect /store and /marketplace paths to /tienda, restoring /store access and preventing 404 errors.

- Added CSRF macro usage to commerce and admin templates; implemented streak claim API, fixed profile route, paginated feed comments and renamed Referral fields for tests.
- Resolved /tienda 500 by pointing commerce_index to existing template and ensuring query parameters are handled safely.
- Hardened HTTP responses: removed legacy X-Frame-Options/Expires headers and enforced UTF-8 content type and nosniff policy.
- Added /login/verify route with two-factor code validation and corrected login redirect.
- Guarded post_reaction migration to check for posts table before altering and fixed admin sidebar events link.
- Guarded crolars price rendering across store and commerce templates to prevent 500 errors when price is missing (PR store-crolars-undefined).
- Wrapped favorite product price credits section with defined check and "No disponible" fallback to handle missing values.
- Wrapped product detail crolars price block with defined check and "No disponible" fallback (hotfix product-crolars-fallback).
- Guarded cart price credits display and total calculation with defined check and fallback placeholder in `carrito.html`.
- Wrapped product price credits in `store/view_product.html` with defined checks, added "No disponible" fallbacks and disabled actions when missing.
- Guarded product card price credits with defined check, added "No disponible" fallbacks and defaulted data-credits to 0 when undefined.
- Wrapped purchase price credits section with defined check and "No disponible" fallback in `compras.html`.
- Wrapped profile purchases tab price credits with defined check and "No disponible" fallback.
- Replaced `product.price_credits or ''` with `product.price_credits if product.price_credits is defined else ''` in `admin/manage_store.html`.
- Replaced `product.price_credits if product else ''` with `product.price_credits if product and product.price_credits is defined else ''` in `admin/add_edit_product.html`.
- Added Jinja macro `render_price_credits` in `components/price_credits.html` to display price credits or 'No disponible'; replaced templates to use it and set `Product.price_credits` default to 0. Use `render_price_credits(obj)` for future displays.
- Guarded product detail and card templates against undefined `price`, showing "Precio no disponible" when missing and hiding cart actions accordingly.
- Added accessible labels and hidden text to product card icon buttons to satisfy button accessibility checks.
- Wrapped `backdrop-filter` usage in `store.css` with `@supports` fallbacks for broader browser compatibility.
- Restored `X-Frame-Options` security header.
- Restored `/feed` URL after closing photo modal, added direct route cleanup and ensured back button closes modal (PR feed-modal-url-fix).
- Updated all navigation links and cart scripts to use `/tienda` directly, replacing legacy `/store` paths that filtered out marketplace products. Cart badge and search results now call commerce endpoints. (PR navbar-store-direct)
- Added placeholder migration cd14a01e631b to resolve missing revision during deployment.

- Guarded `complete_missing_models` migration against absent tables and aligned
  saved courses table name, preventing `NoSuchTableError` on deployments.
- Guarded `add_user_career_interests` migration against missing `users` table
  by checking for table existence before altering.
- Computed cart totals server-side and guarded price display to prevent /tienda/cart 500 errors.
- Logged missing profile users and returned 404 instead of 500; wrapped profile queries in try/except to handle absent tables gracefully (PR perfil-500-fix).
- Defaulted `verification_level` to 0 in profile logic and templates to prevent 500 errors when user records store NULL values.
- Guarded profile note statistics against missing ratings to avoid `/perfil/<username>` 500 errors.
- Filtered non-numeric note ratings and averaged safely to prevent division errors on profile; added tests for profiles with and without notes (PR profile-average-rating-fix).
- Added fallback `rating` property on `Note` and strengthened profile stats calculations with numeric checks and safe queries to prevent `/perfil/<username>` 500 errors.
