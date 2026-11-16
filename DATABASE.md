# DATABASE.md

## Entidades principales previstas

### 1. usuarios (users)
**ID**: user_id (PK)
**Atributos**: username, email, password_hash, is_seller, is_verified, created_at, last_login_at, preferences_json
**Responsabilidades**: Autenticación base, datos de perfil compartidos para compradores y vendedores, configuración de account

### 2. vendedores (sellers)
**ID**: seller_id (PK, FK hacia users)
**Atributos**: store_name, business_name, tax_id, payment_info_json, bank_account, is_verified, created_at, last_login_at
**Responsabilidades**: Registro de vendedores, configuración de negocio, aislamiento de contabilidad, datos de pago (simulados)

### 3. tiendas (stores)
**ID**: store_id (PK)
**Atributos**: seller_id (FK), name, description, slug, logo_url, cover_image_url, is_active, created_at, updated_at
**Responsabilidades**: Administre de tiendas, página de storefront, imágenes, configuración de tienda

### 4. categorías (categories)
**ID**: category_id (PK)
**Atributos**: name, description, slug, parent_id, level, path, is_active, created_at
**Responsabilidades**: Organización del catálogo de productos, jerarquía, management de etiquetas

### 5. productos (products)
**ID**: product_id (PK)
**Atributos**: store_id (FK), category_id (FK), name, description, price, cost, sku, stock, is_active, images_urls, created_at, updated_at
**Responsabilidades**: Catálogo de productos, inventario, pricing, imágenes

### 6. carritos (carts)
**ID**: cart_id (PK)
**Atributos**: user_id (FK), created_at, expires_at, last_updated_at
**Responsabilidades**: Gestión temporal de compras, sincronización entre dispositivos

### 7. items_carrito (cart_items)
**ID**: cart_item_id (PK)
**Atributos**: cart_id (FK), product_id (FK), quantity, price_at_time, created_at
**Responsabilidades**: Gestión de productos en carrito, cálculo de precios, tracking de quantities

### 8. pedidos (orders)
**ID**: order_id (PK)
**Atributos**: user_id (FK), total_amount, status, payment_status, created_at, updated_at
**Responsabilidades**: Pedido principal, cálculo de total, tracking de estado, cálculo de comisiones

###  fascia 9. 10. items_pedido (order_items)
**ID**: order_item_id (PK)
**Atributos**: order_id (FK), product_id (FK), quantity, price, seller_id, created_at
**Responsabilidades**: Items individuales de pedido, asignación por vendedor, cálculo de subpedidos

### 11. subpedidos (order_subitems)
**ID**: order_subitem_id (PK)
**Atributos**: order_id (FK), seller_id, subtotal, commission, status, created_at
**Responsabilidades**: Cálculo de subpedidos, cálculo de comisiones por vendedor, tracking de estados individuales

### 12. pagos (payments)
**ID**: payment_id (PK)
**Atributos**: order_id (FK), amount, method, status, transaction_id, processed_at, created_at
**Responsabilidades**: Procesamiento de pagos simulados, registro de transacciones, tracking de reembolsos

### 13. comisiones (commissions)
**ID**: commission_id (PK)
**Atributos**: seller_id (FK), order_subitem_id (FK), amount, status, paid_at, created_at
**Responsabilidades**: Cálculo y tracking de comisiones, registro de pagos a vendedores

### 14. reseñas_productos (product_reviews)
**ID**: review_id (PK)
**Atributos**: product_id (FK), user_id (FK), rating, title, content, is_approved, created_at, updated_at
**Responsabilidades**: Reseñas de productos, rating system, moderación de contenido

### 15. reseñas_tiendas (store_reviews)
**ID**: store_review_id (PK)
**Atributos**: store_id (FK), user_id (FK), rating, title, content, is_approved, created_at, updated_at
**Responsabilidades**: Reseñas de tiendas, rating de storefronts, moderación de contenido

### 16. inventarios (inventories)
**ID**: inventory_id (PK)
**Atributos**: product_id (FK), store_id (FK), quantity, reserved_quantity, last_updated_at
**Responsabilidades**: Control de stock, tracking de cantidades, validación de disponibilidad

### 17. notificaciones (notifications)
**ID**: notification_id (PK)
**Atributos**: user_id (FK), title, message, type, is_read, related_entity_type, related_entity_id, created_at
**Responsabilidades**: Sistema de notificaciones, alertas del sistema, confirmations

### 18. credenciales_pago (payment_credentials)
**ID**: credential_id (PK)
**Atributos**: seller_id (FK), provider, card_data_encrypted, is_default, created_at, updated_at
**Responsabilidades**: Gestión de tarjetas de pago, datos cifrados (simulados)

## Relaciones entre entidades

### Relaciones uno a muchos
- **usuarios → vendedores**: Un usuario puede ser vendedor (opcional), FK seller_id en usuarios
- **usuarios → pedidos**: Un usuario puede tener múltiples pedidos, FK user_id en pedidos
- **usuarios → carritos**: Un usuario puede tener múltiples carritos activos, FK user_id en carritos
- **usuarios → reseñas_productos**: Un usuario puede escribir múltiples reseñas, FK user_id en reseñas_productos
- **usuarios → reseñas_tiendas**: Un usuario puede escribir múltiples reseñas de tiendas, FK user_id en reseñas_tiendas
- **usuarios → notificaciones**: Un usuario recibe múltiples notificaciones, FK user_id en notificaciones
- **vendedores → tiendas**: Un vendedor puede tener múltiples tiendas, FK seller_id en tiendas
- **vendedores → comisiones**: Un vendedor recibe múltiples comisiones, FK seller_id en comisiones
- **vendedores → credenciales_pago**: Un vendedor guarda múltiples métodos de pago, FK seller_id en credenciales_pago
- **tiendas → productos**: Una tienda puede tener múltiples productos, FK store_id en productos
- **tiendas → reseñas_tiendas**: Una tienda recibe múltiples reseñas, FK store_id en reseñas_tiendas
- **tiendas → inventarios**: Una tienda mantiene inventario para productos, FK store_id en inventarios
- **tiendas → notificaciones**: Una tienda puede recibir notificaciones, FK store_id en notificaciones
- **categorías → productos**: Una categoría puede tener múltiples productos, FK category_id en productos
- **categorías → subcategorías**: Jerarquía de categorías, auto-relación via parent_id
- **productos → items_carrito**: Un producto puede estar en múltiples carritos, FK product_id en items_carrito
- **productos → items_pedido**: Un producto puede aparecer en múltiples pedidos, FK product_id en items_pedido
- **productos → reseñas_productos**: Un producto recibe múltiples reseñas, FK product_id en reseñas_productos
- **productos → inventarios**: Un producto tiene inventario en tiendas, FK product_id en inventarios
- **carritos → items_carrito**: Un carrito tiene múltiples items, FK cart_id en items_carrito
- **pedidos → items_pedido**: Un pedido tiene múltiples items, FK order_id en items_pedido
- **pedidos → pagos**: Un pedido tiene un pago, FK order_id en pagos
- **pedidos → subpedidos**: Un pedido tiene múltiples subpedidos, FK order_id en subpedidos
- **pedidos → notificaciones**: Un pedido puede generar notificaciones, FK order_id en notificaciones
- **subpedidos → comisiones**: Un subpedido genera una comisión, FK order_subitem_id en comisiones
- **subpedidos → notificaciones**: Un subpedido puede generar notificaciones, FK order_subitem_id en notificaciones

### Relaciones muchos a muchos (implícitas)
- **productos ↔ usuarios (via reseñas_productos)**: Un producto recibe reseñas de múltiples usuarios
- **tiendas ↔ usuarios (via reseñas_tiendas)**: Una tienda recibe reseñas de múltiples usuarios

## Responsabilidades de cada entidad

### Entidades base de negocio
- **productos**: Desarrollo de catálogo, gestión de inventario, definición de pricing
- **pedidos**: Gestión del ciclo de vida de compras, cálculo de totales, tracking financiero
- **vendedores**: Registro y verificación de negocios, administración de tiendas

### Entidades de apoyo
- **usuarios**: Autenticación base, perfiles, preferencias
- **tiendas**: Presencia de storefront, branding, configuración
- **categorías**: Organización del catálogo, navegación

### Entidades transaccionales
- **carritos**: Gestión temporal de compras, cálculos de precios en tiempo real
- **items_carrito**: Detalle de selección de productos, cálculo de subtotales

### Entidades financieras
- **pagos**: Procesamiento de transacciones, tracking de reembolsos
- **comisiones**: Cálculo de pagos a vendedores, contabilidad

### Controles y calidad
- **inventarios**: Control de stock, validación de disponibilidad
- **reseñas_productos**: Feedback de usuarios, calificaciones
- **reseñas_tiendas**: Reputación de tiendas, calidad de servicio

### Interacción
- **notificaciones**: Comunicación con usuarios, alerts del sistema
- **credenciales_pago**: Gestión de tarjetas simuladas

## Consideraciones para pedidos multivendedor e inventario

### Aislamiento de datos entre vendedores
- **Inventario por tienda**: Cada tienda mantiene su propio inventario para sus productos
- **Subpedidos por vendedor**: Los pedidos se dividen en subpedidos por vendedor para mantener contabilidad aislada
- **Comisiones por subpedido**: Las comisiones se calculan por cada subpedido, no por el pedido completo
- **Productos de vendedores específicos**: Las relaciones `productos.store_id` y `inventarios.store_id` garantizan que los vendedores solo vean y gestionen sus propios productos

### Control de inventario
- **inventarios** mantiene cantidades por producto y tienda
- **productos** mantiene stock general por producto (proyecto futuro)
- **items_carrito** valida disponibilidad en tiempo real
- **items_pedido** reserva cantidades al crear pedido
- **inventarios** actualiza cantidades después de pedido completado

### Deduplicación de datos
- **productos** almacena información maestra (una vez por producto)
- **inventarios** almacena cantidades por tienda (muchos a uno)
- **items_carrito** almacena precios y cantidades temporales
- **items_pedido** almacena snapshots de precios por pedido (histórico)

### Flujo de control de inventario
1. **Verificación en carrito**: `items_carrito` valida disponibilidad consultando `inventarios`
2. **Reserva al crear pedido**: `items_pedido` reserva cantidades en `inventarios`
3. **Entrega**: `items_pedido` disminuye cantidades en `inventarios`
4. **Cancelación**: `items_pedido` devuelve cantidades desde `inventarios`

### Aislamiento de comisiones
- **subpedidos** calcula comisiones por vendedor por pedido
- **comisiones** trackea pagos individuales por seller_id
- Cálculo: `comisiones.amount = subtotal * commission_percentage`
- Pago: `comisiones.paid_at` marca como pagado cuando se procesa

### Planificación futura para escalabilidad
- **Inventario distribuido**: Cada tienda maneja su propio inventario localmente
- **Cálculo de comisiones**: Por backend, validando el cliente antes de la creación
- **Facturación por vendedor**: Cálculos aislados por seller_id
- **Traspasos entre vendedores**: Planificar sistema futuro para inventario compartido

## Puntos de consolidación de datos

### Estadísticas por vendedor
- Consulta JOIN de `subpedidos` por seller_id para revenue total
- JOIN con `comisiones` para tracking de pagos
- JOIN con `productos` para conteo de items vendidos

### Análisis del carrito
- `cart_items` + `productos` para cálculo de totales
- `carts` + `users` para comportamiento de usuarios

### Auditoría financiera
- Consulta JOIN de `pedidos` + `pagos` + `comisiones` + `sellers`
- Rastreo de cada subpedido hasta su comisión

## Restricciones de integridad referencial

- **ON DELETE CASCADE**: 
  - `ON DELETE CASCADE` en `productos.store_id` → `tiendas.store_id`
  - `ON DELETE CASCADE` en `inventarios.store_id` → `tiendas.store_id`
  - `ON DELETE CASCADE` en `inventarios.product_id` → `productos.product_id`
  - `ON DELETE CASCADE` en `resenas_tiendas.store_id` → `tiendas.store_id`
  - `ON DELETE CASCADE` en `resenas_productos.product_id` → `productos.product_id`

- **ON DELETE RESTRICT**:
  - `ON DELETE RESTRICT` en `order_items.seller_id` → `sellers.seller_id` (previene eliminación accidental)
  - `ON DELETE RESTRICT` en `commissions.seller_id` → `sellers.seller_id`
  - `ON DELETE RESTRICT` en `commissions.order_subitem_id` → `order_subitems.order_subitem_id`

## Notas futuras
- No es necesario escribir SQL todavía (según el requerimiento)
- Las migraciones se agregarán cuando se implementen las entidades
- Se agregarán índices para consultas frecuentes
- Se agregará soporte para soft deletes
- Se agregará auditoría de cambios
- Se agregará control de versiones de esquema
