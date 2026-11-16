# Backend - Plataforma de Comercio

Este directorio contiene la implementación del backend de la plataforma de comercio electrónico multivendedor.

## Estructura

```
back/
├── src/              # Código fuente del backend
├── tests/            # Pruebas unitarias y de integración
├── alembic/          # Migraciones de base de datos
├── .env.example      # Plantilla de variables de entorno
├── .gitignore        # Archivos ignorados por Git
├── pyproject.toml    # Configuración del proyecto y dependencias
└── README.md         # Este archivo
```

## Tecnologías

- **Python 3.12+**
- **FastAPI** - Framework web REST API
- **SQLAlchemy 2.0** - ORM para interacción con base de datos
- **Pydantic** - Validación y tipado de esquemas
- **Alembic** - Migraciones de base de datos
- **PostgreSQL** - Base de datos relacional principal
- **JWT** - Autenticación basada en tokens (RS256)
- **Argon2** - Hash seguro de contraseñas
- **Pytest** - Suite de pruebas
- **HTTPX** - Cliente HTTP para llamadas externas

## Instalación

```bash
cd back/

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -e .

# Copiar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones locales
```

## Configuración de base de datos

1. Instalar PostgreSQL localmente
2. Crear base de datos: `plataforma_comercio_dev`
3. Configurar `DATABASE_URL` en `.env`
4. Ejecutar migraciones: `alembic upgrade head`

## Ejecución

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Pruebas

```bash
pytest
```

## Arquitectura

El backend sigue un enfoque de **monolito modular** organizado en módulos:

- **auth-module**: Autenticación y autorización (JWT, Argon2)
- **user-module**: Perfiles de compradores y vendedores
- **seller-module**: Administración de vendedores
- **store-module**: Gestión de tiendas
- **category-module**: Catálogo de categorías
- **product-module**: Catálogo de productos e inventario
- **cart-module**: Carrito de compras
- **order-module**: Gestión de pedidos y subpedidos por vendedor
- **payment-module**: Pagos simulados
- **commission-module**: Sistema de comisiones
- **review-module**: Calificaciones y reseñas
- **notification-module**: Notificaciones
- **admin-module**: Panel de administración

## Seguridad

- Autenticación JWT con RS256
- Hash de contraseñas con Argon2id
- Aislamiento de datos entre vendedores (RLS en PostgreSQL)
- Validación de entradas con Pydantic

## Documentación

Los documentos de arquitectura se encuentran en la raíz del repositorio:
- `ARCHITECTURE.md`
- `DATABASE.md`
- `API_SPECIFICATION.md`
- `SECURITY.md`
- `DEVELOPMENT_PLAN.md`
- `PROGRESS.md`
