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
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=2)  # expira en 2 horas
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token if isinstance(token, str) else token.decode('utf-8')

def verificar_token(token: str):
    print("SECRET_KEY usada para verificar:", SECRET_KEY)
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # token expirado
    except jwt.InvalidTokenError:
        return None  # token inválido
