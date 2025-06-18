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
- Añadidos atributos ARIA al botón de menú para que muestre el icono hamburguesa y funcione la colapsación (PR fix/navbar-toggler).
