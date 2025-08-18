from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from repositories import cambios_estado, comentarios, tickets, usuarios
from services import auth

app = FastAPI()

# Define qué orígenes pueden acceder
origins = [
    "http://localhost:8100",  # Ionic local
    "http://127.0.0.1:8100",  # a veces Ionic sirve con 127
    # "https://tu-dominio.com" # cuando subas a producción
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],  # puedes restringir a ["GET", "POST"]
    allow_headers=["*"],  # puedes especificar ["Authorization", "Content-Type"]
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


# Listar usuarios (solo para pruebas)
@app.get("/usuarios")
def listar_usuarios_endpoint():
    return usuarios.listar_usuarios()


# Tickets
@app.post("/tickets/")
def crear_ticket_endpoint(ticket: dict, request: Request):
    # Obtener el token del header Authorization
    auth_header = request.headers.get("Authorization")
    print("Authorization header:", auth_header)

    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token faltante o inválido")

    token = auth_header.split(" ")[1]
    print("Token a verificar:", token)

    payload = auth.verificar_token(token)
    print("Payload verificado:", payload)

    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")

    # Tomar id_usuario del token
    id_usuario = payload["sub"]

    id_ticket = tickets.crear_ticket(
        id_usuario,
        ticket["titulo"],
        ticket["descripcion"],
        ticket["tipo_problema"],
        ticket["prioridad"],
        ticket.get("dispositivo"),
    )
    return {"id_ticket": id_ticket}


@app.get("/tickets/")
def listar_tickets_endpoint(id_usuario: int = None):
    return tickets.listar_tickets(id_usuario)


@app.get("/tickets/{id_ticket}")
def obtener_ticket_endpoint(id_ticket: int):
    ticket = tickets.obtener_ticket(id_ticket)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket no encontrado")
    return ticket


@app.put("/tickets/{id_ticket}/estado")
def actualizar_estado_ticket_endpoint(id_ticket: int, estado: str):
    tickets.actualizar_estado_ticket(id_ticket, estado)
    return {"status": "actualizado"}


# Comentarios
@app.post("/tickets/{id_ticket}/comentarios")
def agregar_comentario_endpoint(id_ticket: int, data: dict):
    id_comentario = comentarios.agregar_comentario(
        id_ticket, data["id_usuario"], data["comentario"], data.get("archivo_adjunto")
    )
    return {"id_comentario": id_comentario}


@app.get("/tickets/{id_ticket}/comentarios")
def listar_comentarios_endpoint(id_ticket: int):
    return comentarios.listar_comentarios(id_ticket)


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
