# Correcciones y Unificación de Personal Space / Workspace

## 0) Problemas visibles

-   Card "Objetivos activos" sin icono (métricas del dashboard).
-   Modal "Nuevo Bloque" (Personal Space): la pestaña "Desde Plantilla"
    no conmuta ni habilita *Siguiente*; varios botones sin acción.
-   Workspace usa otro modal distinto (y anticuado); quiero el mismo
    modal de Personal Space.
-   "Plantillas" del dashboard abre una galería aparte → debería ser el
    mismo flujo que "Desde Plantilla" dentro del modal "Nuevo Bloque".
-   Drag & Drop: se espera mover bloques libremente solo en modo
    *Edición* y persistir posición; hoy no hay flujo completo ni
    salvaguardas.
-   Console en dashboard: *Blocks grid not found* (se dispara lógica del
    grid fuera de Workspace).

------------------------------------------------------------------------

## 1) Iconografía coherente (rápido)

**Archivos:** personal-space dashboard (template/cards), BlockFactory
(listado de tipos), DEFAULT_ICONS en JS.

-   Añadir icono a Objetivos en dos lugares:
    a)  Tarjeta de métricas del dashboard (usar Bootstrap Icons:
        `bi-bullseye`).\
    b)  Tarjeta de selección de "Objetivos" dentro del modal Nuevo
        Bloque.
-   Alinear mapping central `DEFAULT_ICONS['objectives']='bi-bullseye'`.

**DoD**\
La card "Objetivos activos" y el modal "Nuevo Bloque" muestran el mismo
icono.

------------------------------------------------------------------------

## 2) Unificar un solo modal "Nuevo Bloque"

**Acciones:**\
- Extraer modal de Personal Space a componente compartido.\
- Workspace debe incluir ese mismo modal y eliminar el suyo.\
- JS controlador único (`BlockFactoryController`) con métodos:\
- `show(typeOrTab)`\
- `selectBlockType(type)`\
- `createFromType()`\
- `openTemplateTab()`

**DoD**\
Dashboard y Workspace usan el mismo modal.

------------------------------------------------------------------------

## 3) Pestaña "Desde Plantilla"

-   Conmuta con "Bloque Individual".\
-   Carga galería de plantillas.\
-   Botones de "Crear/Importar Plantilla" → si no implementados:
    deshabilitar con tooltip.\
-   Botón *Plantillas* del dashboard = alias de esta pestaña.

**DoD**\
"Desde Plantilla" funciona con *Siguiente/Crear* habilitado.

------------------------------------------------------------------------

## 4) Botones del modal

-   `selectBlockType(type)` guarda estado y habilita botón *Siguiente*.\
-   Si no hay selección, *Siguiente* permanece deshabilitado.\
-   Revisar que Bootstrap JS esté cargado solo una vez.

**DoD**\
Botón *Siguiente* responde correctamente.

------------------------------------------------------------------------

## 5) Drag & Drop consistente (solo en Editar)

-   Usar GridStack como fuente única.\
-   `toggleEditMode()` → `grid.enable()` / `grid.disable()`.\
-   Guardar posiciones en `saveWorkspace()`.\
-   Evitar inicialización en dashboard.

**DoD**\
Se pueden arrastrar bloques en modo edición y guardar posiciones.

------------------------------------------------------------------------

## 6) Guards para evitar warnings

-   Encapsular lógica del grid con:

    ``` js
    if (!document.querySelector('#workspace-container')) return;
    ```

**DoD**\
Sin *Blocks grid not found* en consola.

------------------------------------------------------------------------

## 7) API Contracts

-   `GET /api/personal-space/templates`\
-   `POST /api/personal-space/templates/{id}/instantiate`\
-   `POST /api/personal-space/blocks`\
-   `PATCH /api/personal-space/blocks/positions`

**DoD**\
Creación de bloques/plantillas refleja en grid y actualiza métricas.

------------------------------------------------------------------------

## 8) UI/UX y accesibilidad

-   Foco visible en tabs y tarjetas.\
-   Tooltips en acciones no implementadas.\
-   Mensajes vacíos claros.\
-   Consistencia de colores (tema claro).

------------------------------------------------------------------------

## 9) QA Checklist

-   Icono de Objetivos visible.\
-   Modal único funciona.\
-   Drag&Drop con persistencia.\
-   Sin errores en consola.

------------------------------------------------------------------------

## 10) DoD Global

-   Modal único compartido.\
-   Objetivos con icono.\
-   Drag&Drop persistente.\
-   Consola limpia.\
-   Experiencia coherente entre vistas.

------------------------------------------------------------------------

## 11) **Mejoras adicionales sugeridas**

-   **Buscador de bloques** dentro del modal (filtrar por nombre/tipo).\
-   **Favoritos/recientes** en el modal para acceso rápido.\
-   **Modo responsive**: grid adaptable a móvil con stack vertical.\
-   **Historial de cambios / undo-redo** para drag&drop.\
-   **Onboarding interactivo** (tooltip guiado en primer uso).\
-   **Notificaciones en tiempo real** cuando otro usuario edite (si se
    habilita colaboración).\
-   **Dark mode opcional** aunque el workspace esté en claro por
    defecto.\
-   **Lazy loading de bloques** para mejorar performance en workspaces
    grandes.\
-   **Tests automáticos**: Cypress/Playwright para validar flujo del
    modal y drag&drop.\
-   **Logging centralizado**: capturar errores JS y enviarlos a un
    servicio (Sentry/Elastic).\
-   **Soporte multi-idioma** en el modal (es/en).\
-   **Atajos de teclado**: por ejemplo, `N` = nuevo bloque, `E` =
    editar, `Esc` = cerrar modal.\
-   **Exportar/Importar Workspace** a JSON/YAML para backup/restore.

------------------------------------------------------------------------

## 12) Futuras extensiones

-   Integrar **analytics**: cuántos bloques se crean, desde plantillas o
    individuales.\
-   **Permisos/roles**: algunos usuarios solo ven, otros editan.\
-   **API pública** para que terceros creen plantillas personalizadas.\
-   **Integración con calendario externo** (Google/Outlook).\
-   **Modo colaborativo** con sockets.

------------------------------------------------------------------------
