# CONTEXTO — Sistema Tickets Rucaray (Backend)

## Stack tecnológico

| Tecnología | Versión | Rol |
|---|---|---|
| Python | 3.10+ | Lenguaje principal |
| FastAPI | Latest | Framework REST API |
| Uvicorn | Latest | Servidor ASGI |
| MySQL / MariaDB | Any | Base de datos relacional |
| mysql-connector-python | Latest | Driver de base de datos |
| PyJWT | Latest | Generación y validación de tokens JWT |
| bcrypt | Latest | Hash de contraseñas |
| python-dotenv | Latest | Variables de entorno desde `.env` |

**Versión actual:** `1.0.0`  
**Compatibilidad frontend:** `1.0.0`

---

## Arquitectura

Patrón Repository con separación en capas:

```
main.py (API Gateway)
├── services/
│   └── auth.py          → Lógica JWT y autenticación
└── repositories/
    ├── tickets.py        → CRUD tickets + auditoría automática
    ├── usuarios.py       → Gestión de usuarios
    ├── ticket_feed.py    → Registro de actividades
    └── cambios_estado.py → Historial de cambios de estado
```

Toda operación de BD pasa por los repositories. `main.py` orquesta endpoints y delega lógica.

---

## Base de datos

**Nombre:** `sistema_tickets`

| Tabla | Descripción |
|---|---|
| `tickets` | Información principal de tickets |
| `usuarios` | Usuarios con contraseñas encriptadas |
| `ticket_feed` | Registro de todas las actividades (comentarios, cambios) |
| `cambios_estado` | Historial específico de transiciones de estado |
| `sla_cumplimiento` | Registro de evaluación SLA por cada cierre de ticket |

---

## Modelos principales

### Ticket
| Campo | Tipo | Notas |
|---|---|---|
| `id_ticket` | INT PK | Auto-incremental |
| `titulo` | VARCHAR | Obligatorio |
| `descripcion` | TEXT | Obligatorio |
| `tipo_problema` | VARCHAR(100) | Nombre descriptivo — debe coincidir con sla_tipos_problema.tipo_problema |
| `prioridad` | VARCHAR | |
| `dispositivo` | VARCHAR | |
| `estado` | ENUM | `abierto`, `en_progreso`, `resuelto`, `cerrado` |
| `id_usuario` | INT FK | Usuario que creó el ticket |
| `fecha_creacion` | DATETIME | |
| `tiempo_objetivo_horas` | INT | Horas máximas de resolución según SLA |
| `fecha_limite_resolucion` | DATETIME | Calculada al crear: `fecha_creacion + tiempo_objetivo_horas` |

### Usuario
| Campo | Tipo | Notas |
|---|---|---|
| `id_usuario` | INT PK | |
| `usuario` | VARCHAR | Username único |
| `contrasena` | VARCHAR | Hash bcrypt con salt único |
| `rol` | ENUM | `admin`, `soporte`, `usuario` |
| `nombre` | VARCHAR | |

---

## Endpoints

| Método | Endpoint | Auth | Descripción |
|---|---|---|---|
| GET | `/` | ❌ | Estado de la API |
| GET | `/version` | ❌ | Versión actual |
| POST | `/login` | ❌ | Autenticación → retorna JWT |
| POST | `/usuarios` | ❌ | Crear usuario |
| GET | `/usuarios` | ✅ | Listar usuarios |
| POST | `/tickets/` | ✅ | Crear ticket (asigna SLA automáticamente) |
| GET | `/tickets/` | ✅ | Listar tickets (filtrado por rol) |
| GET | `/tickets/{id}` | ❌ | Obtener ticket específico |
| PATCH | `/tickets/{id}/estado` | ✅ | Actualizar estado |
| POST | `/tickets/{id}/feed` | ❌ | Agregar comentario al feed |
| GET | `/tickets/{id}/feed` | ❌ | Listar feed del ticket |
| POST | `/tickets/{id}/cambios-estado` | ❌ | Registrar cambio de estado |
| GET | `/tickets/{id}/cambios-estado` | ❌ | Listar historial de estados |

---

## Autenticación

- **Algoritmo:** JWT HS256
- **Expiración:** 2 horas
- **Payload del token:** `{ sub: id_usuario, usuario: username, rol: rol }`
- **Header requerido:** `Authorization: Bearer <token>`
- **Contraseñas:** bcrypt con salt único por usuario

---

## Control de acceso por rol

| Rol | Acceso |
|---|---|
| `admin` | Todos los tickets, todas las operaciones |
| `soporte` | Todos los tickets, todas las operaciones |
| `usuario` | Solo sus propios tickets |

El filtrado por rol se aplica en `repositories/tickets.py` → `listar_tickets()`.

---

## Auditoría automática

Cada operación sobre un ticket genera registros automáticos:
- `ticket_feed` → log de toda actividad (creación, comentarios, cambios)
- `cambios_estado` → historial específico de transiciones de estado

El log es atómico: `repositories/tickets.py` escribe en las 3 tablas en la misma operación.

---

## SLA por tipo de problema

Estructura que relaciona `tipo_problema` → `tiempo_objetivo_horas`. Al crear un ticket:
1. Se detecta el `tipo_problema`
2. Se busca el tiempo máximo correspondiente
3. Se asigna `tiempo_objetivo_horas` y se calcula `fecha_limite_resolucion`

Los tickets existentes no se modifican al cambiar la configuración de SLA.

---

## Ciclo de vida del ticket

```
abierto → en_progreso → resuelto → cerrado
```

Las transiciones son bidireccionales (ej. `resuelto` → `abierto` para reabrir).

---

## Configuración

### Variables de entorno (`.env`)

```
SECRET_KEY=...        # Clave simétrica para firmar JWT
DB_HOST=...           # Host MySQL
DB_USER=...           # Usuario BD
DB_PASSWORD=...       # Contraseña BD
DB_NAME=sistema_tickets
```

### CORS — Orígenes permitidos

```
http://localhost:8100
http://127.0.0.1:8100
http://192.168.4.195:8100
http://192.168.4.246:2000
```

### Ejecución

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## Estado del roadmap

### DONE ✅
- Autenticación JWT + bcrypt
- CRUD tickets con auditoría completa
- Control de acceso por rol
- Filtro, paginación y ordenamiento de tickets
- Restricción de acciones por rol (en revisión frontend)
- Definición de SLA por tipo de problema (integrado con frontend)
- Definición de SLA por tipo de problema (tabla sla_tipos_problema)
- Asignación automática de tiempo objetivo al crear ticket
- Evaluación de cumplimiento SLA al cerrar ticket (tabla sla_cumplimiento)

### EN REVISIÓN 🔄
- Restricción de acciones por usuario/rol

### EN PROGRESO 🚧
- (ninguna)

### BACKLOG (prioridad de arriba hacia abajo, según tablero Trello)
Ver tablero para lista completa — los items de backend relevantes incluyen:
- Evaluación de Cumplimiento SLA al Cerrar Ticket
- Registro Histórico de Cumplimiento SLA
- Cálculo Automático del KPI de Resolución TI
- Exportación de Reporte KPI
- Función de asignación de tickets
- Reporte diario de trabajos
- Horarios de disponibilidad de soporte
- Base de datos para dispositivos informáticos

---

## Pendientes técnicos conocidos

- `GET /tickets/{id}` no requiere autenticación — evaluar si debe protegerse
- Algunos endpoints de feed y cambios-estado no requieren auth — revisar según requerimientos de rol
- CORS hardcodeado en `main.py` — considerar mover a `.env` para flexibilidad en despliegue

---

## Decisiones de arquitectura

| Decisión | Razón |
|---|---|
| Patrón Repository | Desacopla lógica de negocio del acceso a datos |
| Auditoría atómica en repository | Garantiza consistencia sin lógica duplicada en endpoints |
| JWT stateless | Evita almacenamiento de sesión en servidor |
| bcrypt con salt único | Seguridad robusta de contraseñas |
| FastAPI separado del frontend | Escalabilidad post-MVP, despliegue independiente |

---

## Notas de desarrollo

- Rama principal de desarrollo: `dev`
- Rama de producción: `main`
- Flujo: `feature/nombre` → squash & merge a `dev`
- Credenciales y `.env` en `.gitignore`
- Rama `feature/agenda-mantenimiento` creada, en pausa
