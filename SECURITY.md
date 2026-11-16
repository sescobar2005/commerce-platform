# SECURITY.md

## Estrategia de autenticación

### Autenticación JWT
- **Algoritmo**: RS256 (simétrico, asimétrico)
- **Emisor**: El servidor (en base a `ISS` del config)
- **Audiencia**: Frontend (en base a `AUD` del config)
- **Duración**: 15 minutos (acceso), 7 días (refresh)
- **Refresh token**: Rotativo, almacenado en base de datos
- **Revocación**:Blacklist local (Redis), tokens revocados invalidan accesos

### Flujo de autenticación
1. **Registro (`/api/v1/auth/register`)**:
   - Recibir username, email, password
   - Validar con Pydantic (ej: formato email, longitud password)
   - Hashear password con Argon2 (argon2_id or argon2id)
   - Guardar en `usuarios` tabla
   - Retornar access_token + refresh_token

2. **Inicio de sesión (`/api/v1/auth/login`)**:
   - Validar username/email + password
   - Verificar password con Argon2
   - Generar JWT access_token (15min)
   - Generar JWT refresh_token (7días)
   - Guardar refresh_token en base de datos
   - Retornar tokens

3. **Cierre de sesión (`/api/v1/auth/logout`)**:
   - Invalidar refresh_token via blacklist
   - Eliminar refresh_token de base de datos
   - Retornar success

4. **Validación de token**:
   - Middleware intercepta todas las rutas protegidas
   - Verificar JWT en header `Authorization: Bearer {token}`
   - Verificar en blacklist (si está revocado)
   - Extraer user_id y claim del token
   - Cargar usuario de base de datos
   - Adjuntar al request context

### Recuperación de contraseña
- **Flow**: `POST /api/v1/auth/forgot-password` + `POST /api/v1/auth/reset-password`
- **Rate limit**: 5 intentos por hora por IP
- **Email de recuperación**: Token temporal (1 hora)
- **Cambio de password**: Invalidar tokens previos
- **Tokens seguros**: No reutilizar tokens previos tras cambio de password

## Autorización y roles

### Roles de usuarios
- **user** (comprador): Acceso base, puede comprar, escribir reseñas
- **seller** (vendedor): Gestión de tienda, productos, pedidos, inventario
- **admin**: Acceso completo a todo el sistema
- **moderator**: Administración de contenido, moderación de reseñas

### Esquema de roles
```sql
usuarios.is_seller BOOLEAN DEFAULT FALSE,
usuarios.is_verified BOOLEAN DEFAULT FALSE,
usuarios.is_admin BOOLEAN DEFAULT FALSE,
usuarios.is_moderator BOOLEAN DEFAULT FALSE
```

### Autorización por rol
- **Rutas protegidas**:
  - `POST /api/v1/sellers/`: Solo users no vendedores pueden registrar
  - `PUT /api/v1/users/{user_id}`: Solo propio user_id
  - `GET/PUT /api/v1/sellers/{seller_id}`: Solo el dueño del seller_id
  - `GET/PUT /api/v1/stores/{store_id}`: Solo el dueño del store_id
  - `GET /api/v1/admin/`: Solo administradores
  - `PUT /api/v1/orders/{order_id}/status`: Solo admin o vendedor del order

### Comprobación de permisos
- **Dueño del recurso**: `user_id` del request == `resource.user_id`
- **Seller isolation**: `store.seller_id` == `seller_id` del request o `is_admin`
- **Admin override**: `is_admin` del request permite todo
- **Role-based**: `is_seller`, `is_moderator`, `is_admin` verificados

## Protección de contraseñas con Argon2

### Configuración
- **Algoritmo**: argon2id (nivel más alto de seguridad)
- **Hash**: Formato estándar: `$argon2id$v=19$m=65536,t=3,p=4$` + salt + hash
- **Salt**: Aleatorio por usuario, 16 bytes
- **Parámetros**:
  - Memory: 64MB (65536 KB)
  - Iterations: 3
  - Parallelism: 4
  - Hash length: 32 bytes

### Uso en código
```python
from argon2 import PasswordHasher

ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)

# Hashear
password_hash = ph.hash(password)

# Verificar
ph.verify(password_hash, password)
ph.verify(password_hash, password, tolerate_milliseconds=50)
```

### Seguridad
- **No almacenar plaintext**: Solo hash
- **No reutilizar salts**: Generar salt aleatorio por usuario
- **Rate limit**: 5 intentos por usuario por hora para login
- **Enumerar usuarios**: No indicar si email existe en registro
- **RANGO de hash**: Usar parámetros altos para prevenir ataques GPU
- **Verificación lenta**: Tiempo de hash ~100ms en CPU de servidor

## Uso de JWT

### Configuración JWT
- **Algoritmo**: RS256 (asimétrico)
- **Issuer**: `plataforma-comercio-server`
- **Audience**: `plataforma-comercio-frontend`
- **Secret**: Clave privada RSA-2048, protegida con variables de entorno
- **Expiry**: 15 minutos (access), 7 días (refresh)

### Estrategia de tokens
- **Access token**: corto tiempo, contenido: `user_id, username, role, exp, iat`
- **Refresh token**: largo tiempo, almacenado en base de datos, random
- **Revocación**: Refresh token inválido permite revocar acceso sin access token

### Validación
```python
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(HTTPBearer)):
    # Decodificar y verificar JWT
    # Cargar usuario de la base de datos
    # Retornar usuario
```

## Aislamiento de datos entre vendedores

### Aislamiento de base de datos
- **Row-level security**: Cada query filtrado por `seller_id` apropiado
- **Función de rows**: `is_seller_of_store(store_id)` retorna bool
- **Políticas**: RLS habilitado, restricción por rol

### Comprobaciones de autorización
- **Access control list**: Lista negra/blanca por seller_id
- **Vistas materializadas**: `v_products_by_seller` filtrado automáticamente
- **Debug mode**: No mostrar datos de otros vendedores en logs

### Aislamiento por módulo
- **seller-module**: Solo datos del seller dueño
- **store-module**: Solo tiendas del seller
- **product-module**: Solo productos de tiendas del seller
- **order-module**: Solo pedidos/subpedidos de productos del seller
- **commission-module**: Solo comisiones del seller

### Escenarios de seguridad
- **Seller A** no puede ver **Seller B** sus productos o pedidos
- **Admin** puede ver todo (con restricciones audit)
- **Seller** solo puede modificar sus propios datos
- **Users** pueden solo ver productos y crear pedidos

## Validación de entradas y protección de información

### Validación de entradas
- **Request body**: Validado via Pydantic schemas
- **Path params**: Validados como UUIDs/strings
- **Query params**: Validados con rangos apropiados
- **Headers**: Validados (Authorization, Content-Type)

### Saneamiento de entradas
- **SQL injection**: Prevido via SQLAlchemy ORM
- **XSS**: Prevido via sanitización HTML en frontend
- **CSRF**: JWT elimina necesidad de CSRF para API
- **Buffer overflow**: Prevido via validación de tamaño de entrada

### Limitación de rate
- **Global**: 100 requests por minuto por IP
- **Login**: 5 intentos por usuario por hora
- **Register**: 1 intento por email por hora
- **Password reset**: 3 intentos por usuario por hora

### Protección de datos sensibles
- **Password hash**: Argon2, salt aleatorio
- **Datos de pago**: Tokenización en servicios de pago externos
- **Información personal**: Cifrado en tránsito (HTTPS), cifrado en reposo (TLS)
- **Logs**: No loggear contraseñas, tokens, datos de pago

### Auditoría y monitoreo
- **Accesos fallidos**: Loggear intentos de login fallidos
- **Datos sensibles**: Enmascarar en logs (ej: email → us***@***.com)
- **Cambios de datos**: Loggear cambios en tablas importantes (usuarios, pedidos)
- **Monitoreo**: Detección de patrones anómalos (ej: múltiples logins fallidos)

### TLS y HTTPS
- **Todos los endpoints**: Solo HTTPS en producción
- **HSTS**: Implementado (max-age: 31536000)
- **Cifrado**: TLS 1.2+, prefiriendo cifrados perfectos forward
- **Certificados**: Let's Encrypt o certificado corporativo

## Protección de datos personales

### RGPD/LGPD compliance
- **Consentimiento**: Obtener consentimiento explícito para datos personales
- **Acceso de datos**: Endpoints para que usuarios accedan/eliminen sus datos
- **Portabilidad de datos**: Exportar datos en formato JSON legible por máquina
- **Retención**: Políticas de retención para datos personales (ej: 1 año)
- **Borrado**: Eliminar datos en 30 días tras eliminación de cuenta

### Flujo de consentimiento
1. **Registro**: Consentimiento para marketing (checkbox separado)
2. **Cookies**: Banner de cookies con aceptación granular
3. **Email**: Doble opt-in para emails promocionales
4. **Datos de terceros**: No compartir sin consentimiento explícito

### Retención de datos
- **Usuarios**: Mantener por 1 año tras última actividad
- **Pedidos**: Mantener por 5 años (contabilidad)
- **Inventario**: Mantener por 6 meses
- **Reseñas**: Mantener por 3 años
- **Logs**: Mantener por 30 días

## Seguridad de base de datos

### Configuración de PostgreSQL
- **SSL**: TLS obligatorio para conexiones
- **Autenticación**: Contraseñas fuertes, LIMIT USER
- **Permiso mínimo**: Usuarios con SOLO lectura/escritura necesarios
- **Backups**: Cifrado AES-256, almacenados en S3
- **Monitoreo**: Auditoría de cambios, detección de intentos de acceso

### Access control
- **Least privilege**: Cada usuario/módulo tiene permisos mínimos
- **Role-based**: Usuarios específicos para operaciones
- **Row-level**: RLS para filtrar filas por seller_id

## Resumen de medidas de seguridad

1. **Autenticación**: JWT + Refresh tokens + Argon2 password hash
2. **Autorización**: Role-based + row-level security + owner checks
3. **Input validation**: Pydantic + sanitización + SQL injection prevention
4. **Data protection**: HTTPS/TLS + cifrado en tránsito + HTTPS only
5. **Access control**: JWT + seller isolation + admin override
6. **Rate limiting**: Global + login + register + password reset limits
7. **Audit trails**: Logs de accesos + cambios de datos + datos enmascarados
8. **Password security**: Argon2id + salt aleatorio + hashing lento
9. **Data retention**: Políticas según regulaciones + borrado seguro
10. **Compliance**: RGPD/LGPD + HTTPS + GDPR-compatible
