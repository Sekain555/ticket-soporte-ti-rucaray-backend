import jwt
import datetime
from dotenv import load_dotenv
from fastapi import Request, HTTPException, status
import os

load_dotenv()

# Clave secreta para codificar los tokens
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"


def crear_token(usuario: dict):
    payload = {
        "sub": str(usuario["id_usuario"]),  # id del usuario
        "usuario": usuario["usuario"],
        "rol": usuario["rol"],
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(hours=2),  # expira en 2 horas
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token if isinstance(token, str) else token.decode("utf-8")


def verificar_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception as e:
        print("Error al verificar token:", repr(e))
        return None
    except jwt.ExpiredSignatureError:
        return None  # token expirado
    except jwt.InvalidTokenError:
        return None  # token inválido


def _extraer_token_de_header(request: Request) -> str:
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token faltante",
        )

    parts = auth_header.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Formato Authorization inválido (usa 'Bearer <token>')",
        )
    return parts[1]


def obtener_payload(request: Request) -> dict:
    token = _extraer_token_de_header(request)
    payload = verificar_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
        )
    return payload


def obtener_usuario_desde_request(request: Request) -> dict:
    payload = obtener_payload(request)

    sub = payload.get("sub")
    rol = payload.get("rol")
    usuario = payload.get("usuario")

    if sub is None or rol is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sin 'sub' o 'rol'",
        )

    try:
        id_usuario = int(sub)  # tu 'sub' se guarda como string en el token
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Subject (sub) inválido",
        )

    return {
        "id_usuario": id_usuario,
        "rol": rol,
        "usuario": usuario,
        "payload": payload,
    }
