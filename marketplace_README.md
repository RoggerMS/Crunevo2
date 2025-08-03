# Crunevo Marketplace

Este documento describe la implementación del sistema de Marketplace para Crunevo, que permite a los usuarios registrarse como vendedores, publicar productos y comunicarse con compradores potenciales.

## Características principales

- **Registro de vendedores**: Los usuarios pueden registrarse como vendedores proporcionando información de su tienda, logo y banner.
- **Gestión de productos**: Los vendedores pueden añadir, editar y eliminar sus productos.
- **Panel de vendedor**: Dashboard con estadísticas de ventas, productos y mensajes.
- **Filtros avanzados**: Los compradores pueden filtrar productos por categoría, precio, condición, etc.
- **Sistema de mensajería**: Comunicación directa entre compradores y vendedores.
- **Perfiles de vendedor**: Páginas públicas para cada vendedor con sus productos y valoraciones.

## Estructura de archivos

### Rutas y controladores

- `crunevo/routes/marketplace_routes.py`: Define todas las rutas del marketplace.

### Modelos de datos

- `crunevo/models/marketplace.py`: Define los modelos para vendedores, productos, imágenes, ventas, conversaciones y mensajes.

### Plantillas

- `crunevo/templates/marketplace/`: Contiene todas las plantillas HTML para el marketplace.
  - `index.html`: Página principal del marketplace con filtros y listado de productos.
  - `view_product.html`: Página de detalle de producto.
  - `seller.html`: Perfil público de vendedor.
  - `seller_dashboard.html`: Panel de control para vendedores.
  - `seller_products.html`: Gestión de productos para vendedores.
  - `add_product.html`: Formulario para añadir productos.
  - `edit_product.html`: Formulario para editar productos.
  - `messages.html`: Lista de conversaciones.
  - `view_conversation.html`: Vista de una conversación específica.
  - `become_seller.html`: Formulario para registrarse como vendedor.

### Estilos y JavaScript

- `crunevo/static/css/marketplace.css`: Estilos específicos para el marketplace.
- `crunevo/static/js/marketplace.js`: Funcionalidades interactivas del marketplace.

### Utilidades y formularios

- `crunevo/utils/marketplace_utils.py`: Funciones auxiliares para el marketplace.
- `crunevo/forms/marketplace_forms.py`: Formularios para el marketplace.

## Flujo de trabajo

### Compradores

1. Navegan por el marketplace y filtran productos.
2. Ven detalles de productos y perfiles de vendedores.
3. Pueden contactar a vendedores a través del sistema de mensajería.
4. Pueden comprar productos directamente.

### Vendedores

1. Se registran como vendedores a través de "Become a Seller".
2. Acceden a su panel de vendedor.
3. Añaden y gestionan sus productos.
4. Responden a mensajes de compradores potenciales.
5. Visualizan estadísticas de ventas y productos.

## Integración con el sistema existente

El marketplace se integra con el sistema existente de Crunevo mediante:

- Uso de los modelos de usuario existentes.
- Integración con las categorías y subcategorías de productos existentes.
- Compatibilidad con el sistema de carrito de compras existente.
- Diseño coherente con la estética general de Crunevo.

## Consideraciones técnicas

- Las imágenes se optimizan automáticamente para mejorar el rendimiento.
- Se implementa paginación y carga infinita para mejorar la experiencia de usuario.
- Los productos requieren aprobación antes de ser publicados.
- Se incluyen validaciones de datos en todos los formularios.

## Futuras mejoras

- Sistema de valoraciones para vendedores.
- Estadísticas más detalladas para vendedores.
- Opciones de promoción de productos.
- Integración con sistemas de pago adicionales.
- Notificaciones en tiempo real para mensajes nuevos.