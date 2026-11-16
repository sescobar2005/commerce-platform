# ARCHITECTURE.md

## Visión general del sistema

**Plataforma de Comercio** es un sistema de comercio electrónico multivendedor donde múltiples vendedores pueden administrar sus propias tiendas y productos, mientras los compradores pueden explorar productos, gestionar carritos y realizar pedidos.

## Arquitectura elegida

**Monolito modular**: El backend está organizado como un monolito cuidadosamente dividido en módulos, cada uno con responsabilidades bien definidas. Esta arquitectura equilibra la simplicidad de un monolito con la mantenibilidad de una arquitectura modular.

## Tecnologías y responsabilidades

### Backend (Python 3.12+)
- **FastAPI**: Framework web REST API
- **SQLAlchemy 2.0**: ORM para interacción con base de datos
- **Pydantic**: Validación y tipado de esquemas
- **Alembic**: Migraciones de base de datos
- **PostgreSQL**: Base de datos relacional principal
- **JWT**: Autenticación basada en tokens
- **Argon2**: Hash seguro de contraseñas
- **Pytest**: Suite de pruebas
- **HTTPX**: Cliente HTTP para llamadas externas

### Frontend (Next.js)
- **Next.js**: Framework SSR/RSC
- **TypeScript**: Tipado estático
- **Tailwind CSS**: Estilos utilitarios

## Organización modular del backend

El backend está dividido en los siguientes módulos:

### 1. auth-module (Autenticación y Autorización)
- Gestión de usuarios (registro, login, logout)
- Validación de credenciales
- Control de sesiones JWT

### 2. user-module (Perfil de usuarios)
- Gestión de perfiles de compradores y vendedores
- Configuración de cuenta
- Preferencias de usuario

### 3. seller-module (Administración de vendedores)
- Registro de nuevos vendedores
- Gestión de tiendas
- Autorización de tiendas
- Datos de pago (simulados)

### 4. store-module (Gestión de tiendas)
- Información de tiendas
- Configuración de tienda
- Gestión de imágenes

### 5. category-module (Catálogo de categorías)
- Definición de categorías de productos
- Jerarquía de categorías
- Gestión de etiquetas

### 6. product-module (Catálogo de productos)
- Gestión de inventario
- Definición de productos
- Imágenes y especificaciones
- Control de stock

### 7. cart-module (Carrito de compras)
- Gestión temporal de productos
- Cálculos de precios
- Sincronización entre dispositivos

### 8. order-module (Gestión de pedidos)
- Creación y seguimiento de pedidos
- Cálculo de comisiones
- Subpedidos por vendedor
- Validación de precios por backend

### 9. payment-module (Pagos simulados)
- Simulación de procesamiento de pagos
- Cálculo de comisiones
- Control de reembolsos

### 10. commission-module (Sistema de comisiones)
- Cálculo de comisiones
- Seguimiento de pagos a vendedores
- Reportes financieros

### 11. review-module (Calificaciones y reseñas)
- Reseñas de productos
- Reseñas de tiendas
- Moderación de contenido

### 12. notification-module (Notificaciones)
- Alertas por email
- Notificaciones en-app
- Alertas del sistema

### 13. admin-module (Panel de administración)
- Estadísticas generales
- Auditoría de sistema
- Gestión de usuarios
- Monitoreo de vendedores

## Comunicación entre frontend y backend

- **API REST**: Endpoints REST tradicionales
- **HTTP**: Protocolo estándar para todas las llamadas
- **JSON**: Formato estándar para request/response payloads
- **JWT**: Token de autenticación en el header Authorization
- **CORS**: Configurado para comunicación cross-origin
- **Versionado**: API v1 (será actualizado a v2 cuando sea necesario)

## Estrategia multivendedor y aislamiento de datos

### Aislamiento de datos
- Cada vendedor solo puede acceder a sus propios datos
- Las tiendas están asociadas a un vendedor específico
- El sistema implementa comprobaciones de permisos

### Diseño de pedidos multivendedor
- **Pedido principal**: Representa la compra completa del comprador
- **Subpedidos**: Cada vendedor recibe su propio subpedido
- **Cálculo por backend**: Los importes de subpedidos son calculados por el backend, no enviados por el cliente
- **Validación**: El backend valida todos los cálculos de precios antes de la creación del pedido

### Flujo de pedidos
1. El comprador agrega productos al carrito desde múltiples vendedores
2. El carrito se valida en tiempo real
3. Al finalizar compra, se calculan importes de subpedidos por vendedor
4. Se crean registros de pedido principal y subpedidos
5. El inventario se actualiza por producto
6. Los pagos son simulados
7. Las comisiones son calculadas y registradas

### Aislamiento de contabilidad
- Cada vendedor mantiene su propia contabilidad (ingresos, comisiones, etc.)
- El sistema trackea pagos a vendedores por subpedido
- Las estadísticas por vendedor son aisladas
- El panel de admin ve datos agregados

## Puntos críticos de diseño

- **Monolito modular**: Equilibrio entre simplicidad y mantenibilidad
- **Cálculo por backend**: Evita fraudes y asegura consistencia
- ** Aislamiento de datos**: Garantiza seguridad y privacidad entre vendedores
- **Simulación de pagos**: Reduce complejidad inicial, permite cambios futuros
- **Subpedidos**: Mantiene contabilidad clara por vendedor
- **Responsabilidades claras**: Cada módulo tiene una única responsabilidad
