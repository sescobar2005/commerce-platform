# API_SPECIFICATION.md

## Convenciones de la API REST

### Formato base
- **Base URL**: `/api/v1/`
- **Prefijo**: `/api/v1`
- **Content-Type**: `application/json` para todas las solicitudes/respuestas
- **Endpoints**: Plural (ej: `/users`, `/products`, `/orders`)
- **Query parameters**: Úsanse para filtros, paginación, ordenamiento
- **Path parameters**: Usados para IDs (`/users/{user_id}`, `/products/{product_id}`)

### Estrategia de versionado
- **Minor version**: Incrementa cuando se agreguen nuevos recursos o changos mayor a la API
- **Patch version**: Incrementa cuando se hagan cambios en modelos request/response sin romper compatibilidad
- **URL scheme**: `/api/v1` (actual), `/api/v2` (futuro si es necesario)
- **Headers de versión**: No usados, solo URL basado

### Response format estándar
```json
{
  "success": true,
  "message": "string | null",
  "data": object | null,
  "timestamp": "ISO8601"
}
```

### Error response format
```json
{
  "success": false,
  "message": "string (descriptivo del error)",
  "errors": [
    {
      "field": "string (campo específico)",
      "message": "string (descripción del error)",
      "code": "string (código de error)"
    }
  ],
  "timestamp": "ISO8601"
}
```

### Códigos de estado HTTP
- **200 OK**: Solicitud exitosa
- **201 CREATED**: Recurso creado exitosamente
- **400 BAD REQUEST**: Datos de solicitud inválidos
- **401 UNAUTHORIZED**: No autenticado
- **403 FORBIDDEN**: No autorizado para este recurso
- **404 NOT FOUND**: Recurso no encontrado
- **409 CONFLICT**: Conflicto (ej: stock insuficiente)
- **500 INTERNAL SERVER ERROR**: Error del servidor

### Errores comunes
- **"NOT_FOUND"**: Recurso no encontrado
- **"INVALID_INPUT"**: Datos de solicitud inválidos
- **"UNAUTHORIZED"**: Sin permisos suficientes
- **"FORBIDDEN"**: Prohibido el acceso
- **"CONFLICT"**: Conflicto (ej: duplicado, stock)
- **"VALIDATION_ERROR"**: Error de validación de datos
- **"INTERNAL_ERROR"**: Error inesperado del servidor

## Organización de endpoints por módulos

### Módulo de autenticación (`/api/v1/auth/`)
- `POST /api/v1/auth/register` (registro de usuario)
- `POST /api/v1/auth/login` (inicio de sesión)
- `POST /api/v1/auth/logout` (cierre de sesión)
- `GET /api/v1/auth/me` (perfil actual)
- `PUT /api/v1/auth/password` (actualización de contraseña)
- `POST /api/v1/auth/refresh` (refresh de token)

### Módulo de usuarios (`/api/v1/users/`)
- `GET /api/v1/users/{user_id}` (obtener perfil de usuario)
- `PUT /api/v1/users/{user_id}` (actualizar perfil)
- `DELETE /api/v1/users/{user_id}` (eliminar cuenta)
- `GET /api/v1/users/{user_id}/orders` (pedidos del usuario)

### Módulo de vendedores (`/api/v1/sellers/`)
- `POST /api/v1/sellers/` (registro de nuevo vendedor)
- `GET /api/v1/sellers/{seller_id}` (obtener vendedor)
- `PUT /api/v1/sellers/{seller_id}` (actualizar vendedor)
- `GET /api/v1/sellers/{seller_id}/stores` (tiendas del vendedor)
- `GET /api/v1/sellers/{seller_id}/stats` (estadísticas del vendedor)

### Módulo de tiendas (`/api/v1/stores/`)
- `POST /api/v1/stores/` (crear tienda)
- `GET /api/v1/stores/{store_id}` (obtener tienda)
- `PUT /api/v1/stores/{store_id}` (actualizar tienda)
- `DELETE /api/v1/stores/{store_id}` (eliminar tienda)
- `GET /api/v1/stores/{store_id}/products` (productos de la tienda)
- `GET /api/v1/stores/{store_id}/stats` (estadísticas de la tienda)

### Módulo de categorías (`/api/v1/categories/`)
- `POST /api/v1/categories/` (crear categoría)
- `GET /api/v1/categories/{category_id}` (obtener categoría)
- `PUT /api/v1/categories/{category_id}` (actualizar categoría)
- `DELETE /api/v1/categories/{category_id}` (eliminar categoría)
- `GET /api/v1/categories/` (listar categorías con paginación)
- `GET /api/v1/categories/{category_id}/products` (productos de categoría)

### Módulo de productos (`/api/v1/products/`)
- `POST /api/v1/products/` (crear producto)
- `GET /api/v1/products/{product_id}` (obtener producto)
- `PUT /api/v1/products/{product_id}` (actualizar producto)
- `DELETE /api/v1/products/{product_id}` (eliminar producto)
- `GET /api/v1/products/` (listar productos con filtros)
- `GET /api/v1/products/search` (búsqueda avanzada)
- `POST /api/v1/products/{product_id}/images` (subir imagen)
- `DELETE /api/v1/products/{product_id}/images/{image_id}` (eliminar imagen)

### Módulo de carritos (`/api/v1/carts/`)
- `POST /api/v1/carts/` (crear carrito)
- `GET /api/v1/carts/{cart_id}` (obtener carrito)
- `PUT /api/v1/carts/{cart_id}` (actualizar carrito)
- `DELETE /api/v1/carts/{cart_id}` (eliminar carrito)
- `POST /api/v1/carts/{cart_id}/items` (agregar item al carrito)
- `PUT /api/v1/carts/{cart_id}/items/{item_id}` (actualizar item)
- `DELETE /api/v1/carts/{cart_id}/items/{item_id}` (eliminar item)
- `POST /api/v1/carts/{cart_id}/validate` (validar carrito)
- `POST /api/v1/carts/{cart_id}/merge/{guest_cart_id}` (fusionar carritos)

### Módulo de pedidos (`/api/v1/orders/`)
- `POST /api/v1/orders/` (crear pedido)
- `GET /api/v1/orders/{order_id}` (obtener pedido)
- `GET /api/v1/orders/` (listar pedidos del usuario)
- `PUT /api/v1/orders/{order_id}/status` (actualizar estado)
- `POST /api/v1/orders/{order_id}/cancel` (cancelar pedido)
- `GET /api/v1/orders/{order_id}/items` (items de pedido)
- `GET /api/v1/orders/{order_id}/subitems` (subpedidos de pedido)

### Módulo de pagos (`/api/v1/payments/`)
- `POST /api/v1/payments/` (procesar pago)
- `GET /api/v1/payments/{payment_id}` (obtener pago)
- `GET /api/v1/payments/{order_id}` (pagos de pedido)
- `POST /api/v1/payments/{payment_id}/refund` (procesar reembolso)

### Módulo de comisiones (`/api/v1/commissions/`)
- `GET /api/v1/commissions/{commission_id}` (obtener comisión)
- `GET /api/v1/sellers/{seller_id}/commissions` (comisiones del vendedor)
- `POST /api/v1/commissions/{commission_id}/mark-paid` (marcar como pagada)

### Módulo de reseñas (`/api/v1/reviews/`)
- `POST /api/v1/reviews/products` (crear reseña de producto)
- `GET /api/v1/reviews/products/{product_id}` (reseñas de producto)
- `POST /api/v1/reviews/stores` (crear reseña de tienda)
- `GET /api/v1/reviews/stores/{store_id}` (reseñas de tienda)
- `PUT /api/v1/reviews/{review_id}` (actualizar reseña)
- `DELETE /api/v1/reviews/{review_id}` (eliminar reseña)

### Módulo de notificaciones (`/api/v1/notifications/`)
- `GET /api/v1/notifications/` (listar notificaciones)
- `GET /api/v1/notifications/{notification_id}` (obtener notificación)
- `PUT /api/v1/notifications/{notification_id}/read` (marcar como leída)
- `DELETE /api/v1/notifications/{notification_id}` (eliminar notificación)

### Módulo de administración (`/api/v1/admin/`)
- `GET /api/v1/admin/stats` (estadísticas generales)
- `GET /api/v1/admin/users` (listar usuarios)
- `GET /api/v1/admin/sellers` (listar vendedores)
- `GET /api/v1/admin/orders` (listar pedidos)
- `GET /api/v1/admin/revenue` (estadísticas de revenue)
- `GET /api/v1/admin/inventory` (audit de inventario)

## Filtros y parámetros de consulta comunes

### Filtrado general
- `?search={term}`: Búsqueda en texto
- `?category={category_id}`: Filtrar por categoría
- `?store={store_id}`: Filtrar por tienda
- `?seller={seller_id}`: Filtrar por vendedor
- `?min_price={number}`: Precio mínimo
- `?max_price={number}`: Precio máximo
- `?sort={field}:{order}`: Ordenar (ej: `sort=price:desc`)
- `?limit={number}`: Límite de resultados (default: 20)
- `?offset={number}`: Offset para paginación

### Filtros específicos por módulo

**Productos:**
- `?in_stock=true/false`: Filtrar productos disponibles
- `?min_quantity={number}`: Cantidad mínima en inventario
- `?max_quantity={number}`: Cantidad máxima en inventario

**Pedidos:**
- `?status={status}`: Filtrar por estado (pending, confirmed, cancelled, etc.)
- `?payment_status={status}`: Filtrar por estado de pago
- `?date_from={date}`: Filtrar pedidos desde fecha
- `?date_to={date}`: Filtrar pedidos hasta fecha

**Reseñas:**
- `?rating_min={number}`: Rating mínimo
- `?rating_max={number}`: Rating máximo
- `?verified_only=true`: Solo reseñas verificadas

## Formatos de validación de datos

### Esquemas request (usar Pydantic)
- **UUIDs**: ISO 8601 para datetime, UUID para IDs
- **Emails**: formato estándar
- **Números**: validación de rangos (precio, quantity)
- **Strings**: longitudes máximas, regex para slugs
- **Bools**: valores booleanos estándar

### Mensajes de error estándar
- **"REQUIRED_FIELD"**: Campo requerido missing
- **"INVALID_FORMAT"**: Formato inválido
- **"DUPLICATE_ENTRY"**: Entry duplicado
- **"INSUFFICIENT_STOCK"**: Stock insuficiente
- **"UNAUTHORIZED_ACCESS"**: Sin permisos suficientes
- **"RATE_LIMIT_EXCEEDED"**: Límite de rate excedado

## Puntos de seguridad

### Requerimientos de autorización
- **JWT**: Token en header `Authorization: Bearer {token}`
- **Seller isolation**: Todas las rutas que involucran a tiendas/validan seller_id
- **Role-based**: Algunos endpoints requieren roles específicos

### Validación de entradas
- **Request body**: Validado via Pydantic schemas
- **Path params**: Validados como UUIDs/strings
- **Query params**: Validados con rangos apropiados
- **Headers**: Validados (Authorization, Content-Type)

### Validación de salidas
- **Campos sensibles**: Removidos de responses (ej: password_hash)
- **Datos filtrados**: Solo datos apropiados mostrados por rol
- **Archivos**: URLs de S3, no datos binarios

## Protocolos
aquí
