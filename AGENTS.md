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
