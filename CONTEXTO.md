# CONTEXTO — Sistema Tickets Rucaray (Frontend)

## Stack tecnológico

| Tecnología | Versión | Rol |
|---|---|---|
| Angular | 20.x | Framework principal SPA |
| Ionic | 8.x | UI components responsivos |
| TypeScript | 5.x | Lenguaje principal |
| RxJS | 7.x | Programación reactiva (Observables) |
| Angular Router | 20.x | Navegación con lazy loading |
| Angular HttpClient | 20.x | Comunicación REST con el backend |
| angular-calendar | Latest | Vista calendario en Agenda de Mantenciones |
| date-fns | Latest | Utilidades de fecha requeridas por angular-calendar |

**Versión actual:** `1.3.0`
**Compatibilidad backend:** `1.3.0`

---

## Arquitectura

SPA con arquitectura en capas:

1. **Presentation Layer** — Page components (una página = un módulo lazy-loaded)
2. **Shared Components** — `ComponentsModule` con componentes reutilizables (ej. `HeaderComponent`)
3. **Service Layer** — Lógica de negocio e integración con API
4. **Guards** — Protección de rutas por autenticación (`AuthGuard`)
5. **Interceptors** — Manejo global de errores HTTP (`AuthInterceptor`)
6. **Infrastructure** — `localStorage` para sesión, Service Worker para PWA

Todos los servicios son `providedIn: 'root'` (singletons globales).

---

## Rutas principales

| Ruta | Componente | Guard |
|---|---|---|
| `/login` | `LoginPage` | ❌ |
| `/panel-principal` | `PanelPrincipalPage` | ✅ AuthGuard |
| `/nuevo-ticket` | `NuevoTicketPage` | ✅ AuthGuard |
| `/mis-tickets` | `MisTicketsPage` | ✅ AuthGuard |
| `/detalle-ticket/:id_ticket` | `DetalleTicketPage` | ✅ AuthGuard |
| `/agenda-mantenimiento` | `AgendaMantenimientoPage` | ✅ AuthGuard |
| `/programar-mantenimiento` | `ProgramarMantenimientoPage` | ✅ AuthGuard |
| `/detalle-agenda-mant/:id_mantencion` | `DetalleAgendaMantPage` | ✅ AuthGuard |
| `/listado-dispositivos` | `ListadoDispositivosPage` | ✅ AuthGuard |
| `/detalle-dispositivo/:id_dispositivo` | `DetalleDispositivoPage` | ✅ AuthGuard |

---

## Servicios core

### AuthService
- Autenticación usuario/contraseña contra el backend
- Almacena en `localStorage`: token JWT, `id_usuario`, nombre, apellido, correo, usuario, rol, tema
- `isLoggedIn()` verifica presencia de token
- `logout()` limpia `localStorage`

### TicketService
- CRUD de tickets vía HTTP
- Retorna Observables para integración reactiva

### MantencionService
- CRUD de mantenciones vía HTTP
- Métodos: `crearMantencion()`, `listarMantenciones()`, `obtenerMantencionPorId()`, `actualizarEstadoMantencion()`, `reprogramarMantencion()`, `obtenerFeedMantencion()`, `agregarComentarioMantencion()`

### DispositivoService
- CRUD de dispositivos informáticos vía HTTP
- Métodos: `listarDispositivos()`, `obtenerDispositivoPorId()`, `crearDispositivo()`, `actualizarDispositivo()`

### PermissionsService
- Verifica permisos por rol para controlar elementos UI
- Roles: `admin`, `soporte`, `usuario`
- Lee rol desde `localStorage` dinámicamente

### AuthGuard
- Verifica `isLoggedIn()` antes de permitir navegación
- Redirige a `/login` si no hay token

### AuthInterceptor
- Intercepta todas las respuestas HTTP
- Detecta error 401 → ejecuta `logout()` y redirige a `/login`

---

## Sesión y autenticación

- Token JWT almacenado en `localStorage`
- Expiración: 8 horas (manejada por el backend)
- Guard bloquea navegación sin token
- Interceptor expulsa al usuario cuando el token expira durante el uso
- Datos de sesión: `token`, `id_usuario`, `nombre`, `apellido`, `correo`, `usuario`, `rol`, `tema`

---

## Flujo de usuario

```
/login → /panel-principal → /nuevo-ticket → (crear) → /detalle-ticket/:id
                          → /mis-tickets → /detalle-ticket/:id
                          → /agenda-mantenimiento → /programar-mantenimiento
                                                  → /detalle-agenda-mant/:id
                          → /listado-dispositivos → /detalle-dispositivo/:id
```

---

## Módulos principales

### Tickets
- Listado con filtro por estado, ordenamiento y paginación
- Creación con redirección automática al detalle tras crear
- Detalle con feed de actividades, cambio de estado, categoría SLA editable
- Semáforo SLA (verde/amarillo/rojo) en listado y detalle
- Mensaje "Sin tickets" cuando no hay resultados

### Agenda de Mantenciones
- Vista Lista: filtro por período (Hoy/Semana/Mes) y estado, navegación ←→
- Vista Calendario: vistas Mes/Semana con angular-calendar, eventos con color por estado
- Switch Lista/Calendario con botones pill personalizados
- Detalle con feed, formulario de reprogramación inline, acciones por rol

### Inventario de Dispositivos
- Grilla 6 columnas desktop / 3 móvil con iconos por tipo (PC/Notebook)
- Filtro por tipo y búsqueda por área
- Ordenamiento por nombre, área o IP
- Detalle con formulario de edición inline para admin/soporte

---

## Convenciones de UI

- **Filtros** — fuera de card, directamente sobre el contenido (patrón "Mis tickets")
- **Switch de vistas** — botones pill personalizados (`.switch-pill` / `.pill-btn`)
- **Avatares en feed** — `width: 32px; height: 32px` definido en SCSS del componente
- **Cards del panel principal** — con sticker ilustrativo y navegación al módulo
- **Detección de plataforma** — `ion-datetime` en móvil, `input` nativo en desktop para fechas/horas

---

## Conexión con backend

URL base de la API (hardcodeada — pendiente mover a `environments/*.ts`):
```
http://127.0.0.1:8000
```

---

## PWA

- Configurada con `manifest.webmanifest` y service worker
- **Estado:** base configurada, no declarada operativa en producción aún

---

## Estado del roadmap

### DONE ✅
- Autenticación con login
- Flujo completo de tickets: listado, creación, detalle
- Paginación, filtro y ordenamiento de tickets
- Control de permisos por rol (PermissionsService)
- SLA: tipos de problema, semáforo, toast diferenciado, visualización en detalle
- Agenda de Mantenciones completa (Cards 1-7 + 3.1 + 3.2)
- Inventario de Dispositivos Informáticos (MVP)
- Fix: foto de perfil sobredimensionada en feed de mantenciones
- Switch Lista/Calendario: mejora visual con botones pill
- AuthGuard + AuthInterceptor para protección de sesión
- Redirección al detalle al crear ticket
- Mensaje "Sin tickets" si no hay resultados
- Barra de búsqueda por términos en Mis tickets (título, descripción, N° ticket)

### BACKLOG (ver Trello para orden completo)
- Unificación del flujo de acceso a tickets (Hub de Funciones)
- Mostrar quién creó el ticket en el listado
- Editar información de ticket (con control por rol)
- Restringir campos obligatorios al crear ticket
- Generar PDFs de reporte por ticket
- Función de asignación de tickets
- Etiquetar usuarios en comentarios @
- Notificaciones: bandeja + sonido + recordatorio mantenciones
- Funciones completas para "admin"
- Histórico de acciones del usuario en su perfil
- Horarios de disponibilidad de soporte
- En dispositivos considerar programas y sistemas
- Vista alternativa listado en dispositivos
- KPI y Reportes SLA (múltiples cards)
- Evaluaciones y solucionadores rápidos
- Infraestructura: URL en environments, CORS en .env, endpoints sin auth, PWA, chat

---

## Pendientes técnicos conocidos

- URL base del backend hardcodeada — pendiente mover a `environments/*.ts`
- PWA operativa pendiente de activación formal en producción

---

## Decisiones de arquitectura

| Decisión | Razón |
|---|---|
| Lazy loading por módulo | Optimiza bundle inicial y startup |
| `ComponentsModule` compartido | Evita duplicación de componentes UI |
| Servicios en root | Singleton global, evita múltiples instancias |
| `localStorage` para sesión | Persistencia simple sin backend de sesión |
| `PermissionsService` centralizado | Control de acceso uniforme en toda la UI |
| AuthGuard + AuthInterceptor | Guard bloquea navegación; interceptor expulsa en 401 |
| Filtrado por período 100% frontend | Sin llamadas extra al backend al navegar entre períodos |
| Detección de plataforma para fechas | ion-datetime en móvil, input nativo en desktop |

---

## Notas de desarrollo

- Rama principal de desarrollo: `dev`
- Rama de producción: `main`
- Flujo: `feature/nombre` → squash & merge a `dev`
- Angular actualizado a 20.x (requerido por angular-calendar)
- angular-calendar + date-fns instalados como dependencias
- Import CSS angular-calendar: `@import "../node_modules/angular-calendar/css/angular-calendar.css"` (ruta absoluta requerida)
- `npm install` puede requerir `--legacy-peer-deps` por conflictos de versiones
- Deepwiki disponible en `deepwiki.com/Sekain555/[repo]`