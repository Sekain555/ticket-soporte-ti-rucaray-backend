import jwt
import datetime
from dotenv import load_dotenv
import os

load_dotenv()

# Clave secreta para codificar los tokens
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

def crear_token(usuario: dict):
    payload = {
        "sub": usuario["id_usuario"],  # id del usuario
        "usuario": usuario["usuario"],
        "rol": usuario["rol"],
        "exp": datetime.datetime.now() + datetime.timedelta(hours=2)  # expira en 2 horas
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verificar_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # token expirado
    except jwt.InvalidTokenError:
        return None  # token inválido
