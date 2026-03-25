# 📗 CHANGELOG — Backend (FastAPI / MySQL)

## [1.1.0] — 2026-03-24

### Added
- Tabla `sla_tipos_problema` con 13 tipos de problema y sus tiempos mínimos y máximos de resolución en horas.
- Columnas `tiempo_objetivo_horas` y `fecha_limite_resolucion` en tabla `tickets`, calculadas automáticamente al crear el ticket según el tipo de problema.
- Tabla `sla_cumplimiento` para registrar el resultado SLA de cada cierre de ticket (`dentro_plazo`, `fuera_plazo`, `sin_sla`), con `fecha_cierre`, `fecha_limite` y `tiempo_real_horas`.
- Endpoint `PATCH /tickets/{id}/tipo-problema` para actualizar la categoría del ticket desde el detalle, con recálculo automático de `tiempo_objetivo_horas` y `fecha_limite_resolucion`.
- Evaluación automática de cumplimiento SLA al cerrar un ticket — resultado retornado en la respuesta del endpoint `PATCH /tickets/{id}/estado`.
- `obtener_ticket()` ahora retorna `sla_tiempo_minimo_horas` mediante LEFT JOIN con `sla_tipos_problema`.

### Changed
- `tipo_problema` en tabla `tickets` migrado de ENUM de códigos cortos a VARCHAR(100) con nombres descriptivos.
- `actualizar_tipo_problema_ticket()` ahora recalcula `tiempo_objetivo_horas` y `fecha_limite_resolucion` al cambiar la categoría, usando `fecha_creacion` como base.
- `actualizar_estado_ticket()` ahora retorna `resultado_sla` al cerrar — `None` en cualquier otro cambio de estado.

### Compatibility
- Probado con Frontend `1.1.0`.

### Notes
- Release completo del grupo funcional **Implementación de SLA**.
- La tabla `sla_cumplimiento` está diseñada para alimentar reportes KPI en versiones futuras.
- El umbral de evaluación SLA usa `fecha_limite_resolucion` calculada al momento de creación del ticket, preservando el valor histórico aunque cambie la configuración SLA posterior.

---

## [1.0.0] — 2026-02-15

### Added
- Implementación formal de control de acceso basado en roles (RBAC) mediante decorator `role_required` en endpoints protegidos.

### Changed
- Limpieza y simplificación del manejo de expiración de tokens JWT.
- Refuerzo en validación de permisos por endpoint.

### Compatibility
- Probado con Frontend `1.0.0`.
- Contrato API mantiene versión `/api/v1`.

### Notes
- Primer release estable en producción.
- Se promueven a estable funcionalidades validadas en versiones beta previas.

---

## [0.9.0-beta.1] — 2025-10-20

### Added
- Filtro de tickets por estado (`abiertos`, `cerrados`, `todos`) mediante parámetro `status`.
- Soporte de paginación en endpoint `/tickets` con parámetros `limit` y `offset`.

### Changed
- Estructura de respuesta actualizada: inclusión de `total`, `limit` y `offset`.
- Mejoras en validaciones de parámetros y manejo de errores.
- Revisión de serialización para campos opcionales.

### Fixed
- Correcciones menores en control de errores y formatos de respuesta JSON.

### Compatibility
- Probado con Frontend `0.10.0-rc.1`.
- Contrato API mantiene compatibilidad con `/api/v1`.

### Notes
- Release beta desplegado para pruebas internas del sistema de soporte TI.
- Versión enfocada en optimización de consultas y control de respuesta.

---

## [0.8.0-beta.1] — 2025-09-28

### Added
- Endpoints principales: `/usuarios`, `/tickets`, `/login`, `/version`.
- CRUD completo de tickets (crear, listar, actualizar, cerrar).
- Autenticación JWT y manejo de roles (`admin`, `soporte`, `usuario_rucaray`).
- Integración inicial con base de datos MySQL/MariaDB.
- Middleware de auditoría para registro de acciones de usuario.

### Changed
- Validaciones de entrada y manejo de errores centralizado.
- Estructura inicial de respuesta JSON unificada.

### Notes
- Primer release beta funcional, base para pruebas de integración con frontend.
- Desplegado en entorno interno (departamentos de informática y estadística).

---

## 📊 Compatibility Matrix

| Frontend | Backend | Estado | Fecha | Notas |
|---|---|---|---|---|
| 1.1.0 | 1.1.0 | ✅ Compatible | 2026-03-24 | Release grupo SLA |
| 1.0.0 | 1.0.0 | ✅ Compatible | 2026-02-15 | Primera versión estable en producción |
| 0.10.0-rc.1 | 0.9.0-beta.1 | ✅ Compatible | 2025-10-20 | Release conjunto en entorno de pruebas |
| 0.9.0-rc.1 | 0.8.0-beta.1 | ✅ Compatible | 2025-09-28 | Versión inicial integrada |