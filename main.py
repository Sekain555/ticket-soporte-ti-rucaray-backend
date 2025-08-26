from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from repositories import cambios_estado, ticket_feed, tickets, usuarios
from services import auth

app = FastAPI()

origins = [
    "http://localhost:8100",  # Ionic local
    "http://192.168.4.195:8100",  # IP local de tu dispositivo móvil
    "http://127.0.0.1:8100",  # a veces Ionic sirve con 127
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],  # puedes restringir a ["GET", "POST"]
    allow_headers=[
        "Authorization",
        "Content-Type",
    ],  # puedes especificar ["Authorization", "Content-Type"]
)


@app.get("/")
def home():
    return {"message": "API de Soporte TI funcionando"}


# Crear usuario (solo Postman)
@app.post("/usuarios")
def crear_usuario_endpoint(data: dict):
    id_usuario = usuarios.crear_usuario(
        data["nombre"],
        data["apellido"],
        data["correo"],
        data["usuario"],
        data["contraseña"],
        data["rol"],
        data["departamento"],
        data["puesto"]
    )
    return {"id_usuario": id_usuario}


# Login
@app.post("/login")
def login(data: dict):
    user = usuarios.autenticar_usuario(data["usuario"], data["contraseña"])
    if not user:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    token = auth.crear_token(user)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id_usuario"],
            "nombre": user["nombre"],
            "apellido": user["apellido"],
            "correo": user["correo"],
            "usuario": user["usuario"],
            "rol": user["rol"],
        },
    }


# Listar usuarios
@app.get("/usuarios")
def listar_usuarios_endpoint():
    return usuarios.listar_usuarios()


# Crear tickets
@app.post("/tickets/")
def crear_ticket_endpoint(ticket: dict, request: Request):
    current = auth.obtener_usuario_desde_request(request)
    id_ticket = tickets.crear_ticket(
        current["id_usuario"],
        ticket["titulo"],
        ticket["descripcion"],
        ticket["tipo_problema"],
        ticket["prioridad"],
        ticket.get("dispositivo"),
    )
    return {"id_ticket": id_ticket}

# Listar tickets
@app.get("/tickets/")
def listar_tickets_endpoint(request: Request):
    payload = auth.obtener_payload(request)
    rol = payload.get("rol")
    id_usuario = payload.get("sub")

    return tickets.listar_tickets(rol, id_usuario)

# Obtener ticket por ID
@app.get("/tickets/{id_ticket}")
def obtener_ticket_endpoint(id_ticket: int):
    ticket = tickets.obtener_ticket(id_ticket)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ticket

# Actualizar estado del ticket
@app.put("/tickets/{id_ticket}/estado")
def actualizar_estado_ticket_endpoint(id_ticket: int, estado: str):
    tickets.actualizar_estado_ticket(id_ticket, estado)
    return {"status": "actualizado"}


# Comentarios y actividades (feed)
@app.post("/tickets/{id_ticket}/feed")
def agregar_comentario_endpoint(id_ticket: int, data: dict):
    id_comentario = ticket_feed.agregar_comentario(
        id_ticket, "comentario", data["id_usuario"], data["comentario"]
    )
    return {"id_comentario": id_comentario}


@app.get("/tickets/{id_ticket}/feed")
def listar_feed_endpoint(id_ticket: int):
    feed = ticket_feed.listar_feed(id_ticket)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed no encontrado")
    return feed


# Cambios de estado
@app.post("/tickets/{id_ticket}/cambios-estado")
def agregar_cambio_estado_endpoint(id_ticket: int, data: dict):
    id_cambio = cambios_estado.agregar_cambio_estado(
        id_ticket, data["id_usuario"], data["estado_anterior"], data["estado_nuevo"]
    )
    return {"id_cambio": id_cambio}


@app.get("/tickets/{id_ticket}/cambios-estado")
def listar_cambios_estado_endpoint(id_ticket: int):
    return cambios_estado.listar_cambios_estado(id_ticket)
