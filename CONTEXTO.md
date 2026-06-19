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

**Versión actual:** `1.3.0`
**Compatibilidad frontend:** `1.4.0`

---

## Arquitectura

Patrón Repository con separación en capas:

```
main.py (API Gateway)
├── services/
│   └── auth.py              → Lógica JWT y autenticación (expiración 8h)
└── repositories/
    ├── tickets.py            → CRUD tickets + auditoría automática + SLA
    ├── usuarios.py           → Gestión de usuarios
    ├── ticket_feed.py        → Registro de actividades de tickets
    ├── cambios_estado.py     → Historial de cambios de estado de tickets
    ├── mantenciones.py       → CRUD mantenciones + validación de conflictos
    ├── mantencion_feed.py    → Registro de actividades de mantenciones
    └── dispositivos.py       → CRUD inventario de dispositivos informáticos
```

Toda operación de BD pasa por los repositories. `main.py` orquesta endpoints y delega lógica.

---

## Base de datos

**Nombre:** `sistema_tickets`

| Tabla | Descripción |
|---|---|
| `tickets` | Información principal de tickets |
| `usuarios` | Usuarios con contraseñas encriptadas |
| `ticket_feed` | Registro de actividades de tickets (comentarios, cambios) |
| `cambios_estado` | Historial de transiciones de estado de tickets |
| `sla_tipos_problema` | Tipos de problema con tiempos mínimos y máximos de resolución |
| `sla_cumplimiento` | Evaluación SLA por cada cierre de ticket |
| `mantenciones` | Agenda de mantenciones con estados y asignación de técnico |
| `mantencion_feed` | Registro de actividades de mantenciones |
| `dispositivos` | Inventario de dispositivos informáticos (PCs y Notebooks) |

---

## Modelos principales

### Ticket
| Campo | Tipo | Notas |
|---|---|---|
| `id_ticket` | INT PK | Auto-incremental |
| `titulo` | VARCHAR | Obligatorio |
| `descripcion` | TEXT | Obligatorio |
| `tipo_problema` | VARCHAR(100) | Nombre descriptivo — debe coincidir con sla_tipos_problema.tipo_problema |
| `prioridad` | VARCHAR | Obligatorio |
| `dispositivo` | VARCHAR | Opcional |
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
| `apellido` | VARCHAR | |
| `departamento` | VARCHAR | |
| `puesto` | VARCHAR | |

### Mantención
| Campo | Tipo | Notas |
|---|---|---|
| `id_mantencion` | INT PK | Auto-incremental |
| `titulo` | VARCHAR | Obligatorio |
| `descripcion` | TEXT | Opcional |
| `id_usuario_solicitante` | INT FK | Usuario que creó la mantención |
| `id_usuario_asignado` | INT FK | Técnico asignado (opcional) |
| `fecha_propuesta` | DATE | |
| `hora_inicio` | TIME | |
| `hora_fin` | TIME | |
| `estado` | VARCHAR | `propuesto`, `confirmado`, `reprogramado`, `cancelado` |
| `notas_soporte` | TEXT | Opcional |
| `fecha_creacion` | DATETIME | |
| `fecha_actualizacion` | DATETIME | |

### Dispositivo
| Campo | Tipo | Notas |
|---|---|---|
| `id_dispositivo` | INT PK | Auto-incremental |
| `nombre_asignado` | VARCHAR | Persona o puesto asignado |
| `area` | VARCHAR | |
| `tipo_equipo` | VARCHAR | `PC`, `Notebook` |
| `marca` | VARCHAR | |
| `procesador` | VARCHAR | |
| `ram` | VARCHAR | |
| `disco_duro` | VARCHAR | |
| `monitor` | TINYINT | 0/1 |
| `antivirus` | TINYINT | 0/1 |
| `rj45` | TINYINT | 0/1 |
| `tipo_lan` | VARCHAR | DHCP / Estática |
| `direccion_ip` | VARCHAR | |
| `mac_wifi` | VARCHAR | |
| `version_windows` | VARCHAR | |
| `tipo_office` | VARCHAR | |
| `nombre_equipo` | VARCHAR | Hostname en red |
| `dominio` | TINYINT | 0/1 |
| `observaciones` | TEXT | |
| `fecha_registro` | DATETIME | |
| `fecha_actualizacion` | DATETIME | |

---

## Endpoints

### Autenticación y usuarios
| Método | Endpoint | Auth | Descripción |
|---|---|---|---|
| GET | `/` | ❌ | Estado de la API |
| GET | `/version` | ❌ | Versión actual |
| POST | `/login` | ❌ | Autenticación → retorna JWT |
| POST | `/usuarios` | ❌ | Crear usuario (solo Postman) |
| GET | `/usuarios` | ✅ | Listar usuarios |

### Tickets
| Método | Endpoint | Auth | Descripción |
|---|---|---|---|
| POST | `/tickets/` | ✅ | Crear ticket (asigna SLA automáticamente) |
| GET | `/tickets/` | ✅ | Listar tickets (filtrado por rol, búsqueda, paginación) |
| GET | `/tickets/{id}` | ❌ | Obtener ticket específico |
| PATCH | `/tickets/{id}` | ✅ | Editar campos del ticket (control por rol) |
| PATCH | `/tickets/{id}/estado` | ✅ | Actualizar estado + evaluación SLA |
| PATCH | `/tickets/{id}/tipo-problema` | ✅ | Actualizar categoría + recalcular SLA |
| POST | `/tickets/{id}/feed` | ❌ | Agregar comentario al feed |
| GET | `/tickets/{id}/feed` | ❌ | Listar feed del ticket |
| POST | `/tickets/{id}/cambios-estado` | ❌ | Registrar cambio de estado |
| GET | `/tickets/{id}/cambios-estado` | ❌ | Listar historial de estados |

### Mantenciones
| Método | Endpoint | Auth | Descripción |
|---|---|---|---|
| POST | `/mantenciones/` | ✅ | Crear mantención (valida conflictos de horario) |
| GET | `/mantenciones/` | ✅ | Listar mantenciones (filtrado por rol) |
| GET | `/mantenciones/{id}` | ✅ | Obtener mantención específica |
| PATCH | `/mantenciones/{id}/estado` | ✅ | Actualizar estado (admin/soporte) |
| PATCH | `/mantenciones/{id}/reprogramar` | ✅ | Reprogramar fecha/hora (valida conflictos) |
| POST | `/mantenciones/{id}/feed` | ✅ | Agregar comentario al feed |
| GET | `/mantenciones/{id}/feed` | ✅ | Listar feed de la mantención |

### Dispositivos
| Método | Endpoint | Auth | Descripción |
|---|---|---|---|
| GET | `/dispositivos/` | ✅ | Listar dispositivos (filtro por tipo y área) |
| GET | `/dispositivos/{id}` | ✅ | Obtener dispositivo específico |
| POST | `/dispositivos/` | ✅ | Crear dispositivo (admin/soporte) |
| PATCH | `/dispositivos/{id}` | ✅ | Actualizar dispositivo (admin/soporte) |

---

## Autenticación

- **Algoritmo:** JWT HS256
- **Expiración:** 8 horas
- **Payload del token:** `{ sub: id_usuario, usuario: username, rol: rol, exp: timestamp }`
- **Header requerido:** `Authorization: Bearer <token>`
- **Contraseñas:** bcrypt con salt único por usuario

---

## Control de acceso por rol

| Rol | Tickets | Mantenciones | Dispositivos |
|---|---|---|---|
| `admin` | Todos + todas las operaciones | Todas + gestión | CRUD completo |
| `soporte` | Todos + todas las operaciones | Todas + gestión | CRUD completo |
| `usuario` | Solo los propios (edición solo si abiertos) | Solo las propias | Solo lectura |

---

## Auditoría automática

**Tickets:**
- `ticket_feed` → log de toda actividad (creación, comentarios, cambios, ediciones)
- `cambios_estado` → historial de transiciones de estado
- `sla_cumplimiento` → resultado SLA al cerrar ticket

**Mantenciones:**
- `mantencion_feed` → log de toda actividad (creación, cambios de estado, reprogramación, comentarios)
- Registro automático en `crear_mantencion()`, `actualizar_estado_mantencion()` y `reprogramar_mantencion()`

---

## SLA por tipo de problema

Al crear un ticket:
1. Se detecta el `tipo_problema`
2. Se busca el tiempo máximo en `sla_tipos_problema`
3. Se asigna `tiempo_objetivo_horas` y se calcula `fecha_limite_resolucion`

Los tickets existentes no se modifican al cambiar la configuración de SLA.
Al editar el `tipo_problema` de un ticket existente, se recalcula el SLA automáticamente.

---

## Ciclo de vida del ticket
```
abierto → en_progreso → resuelto → cerrado
```
Las transiciones son bidireccionales.

## Ciclo de vida de la mantención
```
propuesto → confirmado → cancelado
         ↘ reprogramado ↗
```

---

## Serialización

Los campos `TIME` y `DATE` de MySQL retornan como `timedelta` y `date` de Python — se convierten a string en cada repository:
- `serializar_mantencion()` en `mantenciones.py`
- `serializar_dispositivo()` en `dispositivos.py`

---

## Configuración

### Variables de entorno (`.env`)
```
SECRET_KEY=...
DB_HOST=...
DB_USER=...
DB_PASSWORD=...
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
- Filtro, paginación, ordenamiento y búsqueda de tickets
- Definición de SLA por tipo de problema (tabla sla_tipos_problema)
- Asignación automática de tiempo objetivo al crear ticket
- Evaluación de cumplimiento SLA al cerrar ticket (tabla sla_cumplimiento)
- Recálculo automático de SLA al cambiar categoría del ticket
- Edición de ticket con control por rol y auditoría en feed
- Validación de campos obligatorios al crear ticket (título, descripción, prioridad)
- Mostrar nombre del creador en listado de tickets (JOIN a usuarios)
- Modelo de datos para Agenda de Mantenciones
- Serialización de campos TIME y DATE en mantenciones
- Control de conflictos de horario en mantenciones (HTTP 409)
- Feed de actividades en mantenciones (registro automático + comentarios)
- Flujo de reprogramación con cambio de fecha/hora
- Base de datos para dispositivos informáticos (tabla + importación + CRUD)
- Expiración de token JWT a 8 horas

### BACKLOG
- Proteger endpoints sin autenticación (`GET /tickets/{id}`, feed, cambios-estado)
- Mover CORS a variables de entorno
- Registro Histórico de Cumplimiento SLA
- Cálculo Automático del KPI de Resolución TI
- Exportación de Reporte KPI
- Función de asignación de tickets
- Reporte diario de trabajos
- Horarios de disponibilidad de soporte

---

## Pendientes técnicos conocidos

- `GET /tickets/{id}` no requiere autenticación — pendiente proteger
- Endpoints de feed y cambios-estado no requieren auth — pendiente revisar
- CORS hardcodeado en `main.py` — pendiente mover a `.env`

---

## Decisiones de arquitectura

| Decisión | Razón |
|---|---|
| Patrón Repository | Desacopla lógica de negocio del acceso a datos |
| Auditoría atómica en repository | Garantiza consistencia sin lógica duplicada |
| JWT stateless con expiración 8h | Sin almacenamiento de sesión; 8h = jornada laboral |
| bcrypt con salt único | Seguridad robusta de contraseñas |
| FastAPI separado del frontend | Escalabilidad, despliegue independiente |
| VARCHAR descriptivo en tipo_problema | Legibilidad directa en BD sin capa de traducción |
| tiempo_objetivo_horas en ticket | Preserva historial SLA aunque cambie configuración futura |
| Serialización en repository | Evita errores de tipo timedelta/date en respuestas JSON |
| Validación en FE y BE | FE es primera línea (UX); BE es última línea (seguridad) |

---

## Notas de desarrollo

- Rama principal de desarrollo: `dev`
- Rama de producción: `main`
- Flujo: `feature/nombre` → squash & merge a `dev`
- Credenciales y `.env` en `.gitignore`
- Deepwiki disponible en `deepwiki.com/Sekain555/[repo]`
