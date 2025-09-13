# 🖥️ Sistema de Soporte TI - Rucaray (Backend)

API REST desarrollada con **FastAPI** para la gestión de tickets de soporte técnico.  
Incluye **autenticación JWT**, **control de acceso basado en roles** y **auditoría completa** de todas las operaciones.

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
[![Ask DeepWiki](https://deepwiki.com/badge.svg?style=for-the-badge)](https://deepwiki.com/Sekain555/ticket-soporte-ti-rucaray)

---

## 📚 Tabla de contenidos
- [Características principales](#-características-principales)
- [Endpoints principales](#-endpoints-principales)
- [Arquitectura](#-arquitectura)
- [Base de datos](#-base-de-datos)
- [Configuración](#-configuración)
- [Instalación](#-instalación)
- [Ejecución](#-ejecución)
- [Roles de usuario](#-roles-de-usuario)
- [Seguridad](#-seguridad)
- [Documentación adicional](#-documentación-adicional)
- [Licencia](#-licencia)

---

## 🚀 Características principales

### 🎫 Gestión de Tickets
- Creación, listado, consulta y actualización de estado de tickets.  
- Estados disponibles: **abierto, en_progreso, cerrado**.  
- Control de acceso basado en roles:  
  - `admin` y `soporte` → ven todos los tickets.  
  - `usuario` → solo ve sus propios tickets.  

### 🔐 Autenticación y Seguridad
- Autenticación JWT con expiración de **2 horas**.  
- Encriptación de contraseñas con **bcrypt**.  
- Middleware CORS configurado para entorno local.  

### 📊 Auditoría y Seguimiento
- Registro automático de todas las actividades en `ticket_feed`.  
- Historial de cambios de estado en la tabla `cambios_estado`.  

---

## 📡 Endpoints principales

| Método | Endpoint               | Auth | Descripción                                 |
|--------|------------------------|------|---------------------------------------------|
| GET    | `/`                    | ❌   | Estado de la API                            |
| POST   | `/login`               | ❌   | Autenticación de usuario                    |
| POST   | `/tickets/`            | ✅   | Crear ticket                                |
| GET    | `/tickets/`            | ✅   | Listar tickets (filtrado por rol)           |
| GET    | `/tickets/{id}`        | ❌   | Obtener ticket específico                   |
| PATCH  | `/tickets/{id}/estado` | ✅   | Actualizar estado de un ticket              |

---

## 🏗️ Arquitectura

El sistema sigue el **Patrón Repository** para separar lógica de negocio y acceso a datos.

- `repositories/tickets.py` → Operaciones CRUD de tickets.  
- `repositories/usuarios.py` → Gestión de usuarios y autenticación.  
- `services/auth.py` → Servicios de autenticación JWT.  

---

## 🗄️ Base de datos

**MySQL** con las siguientes tablas principales:

- `tickets` → Información de tickets.  
- `usuarios` → Datos de usuarios (contraseñas encriptadas).  
- `ticket_feed` → Registro de actividades.  
- `cambios_estado` → Historial de cambios de estado.  

---

## ⚙️ Configuración

### Variables de entorno
```env
SECRET_KEY=tu_clave_secreta_jwt
```

### Seguridad
- Algoritmo JWT: **HS256**.  
- Validación estricta de headers de autorización.  
- Contraseñas hasheadas con **bcrypt** + salt único.  

---

## 🛠️ Instalación

Requisitos: Python 3.10+, pip y MySQL en ejecución.

```bash
pip install fastapi uvicorn python-jose[cryptography] bcrypt python-dotenv mysql-connector-python
```

---

## ▶️ Ejecución

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Por defecto, la API se ejecuta en:  
```
http://127.0.0.1:8000
```

---

## 👥 Roles de usuario

- **admin** → Acceso completo a todos los tickets.  
- **soporte** → Acceso completo a todos los tickets.  
- **usuario** → Solo puede ver y gestionar sus propios tickets.  

---

## 🔒 Seguridad

- Tokens JWT con expiración de **2 horas**.  
- Contraseñas seguras con **bcrypt**.  
- CORS habilitado para desarrollo local (compatible con frontend Ionic/Angular).  

---

## 📖 Documentación adicional

- [Authentication & Security](https://github.com/Sekain555/ticket-soporte-ti-rucaray-backend/wiki/Authentication-&-Security)  
- [Data Layer & Repositories](https://github.com/Sekain555/ticket-soporte-ti-rucaray-backend/wiki/Data-Layer-&-Repositories)  
- [Ticket Management](https://github.com/Sekain555/ticket-soporte-ti-rucaray-backend/wiki/Ticket-Management)  

---

## 📜 Licencia

Este proyecto está bajo la licencia **MIT**. Consulta el archivo [LICENSE](LICENSE) para más detalles.
