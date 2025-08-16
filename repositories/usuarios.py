from database import get_connection
import bcrypt

# Crear usuario (para pruebas)
def crear_usuario(nombre, apellido, correo, usuario, contraseña, rol):
    conn = get_connection()
    cursor = conn.cursor()
    salt = bcrypt.gensalt()
    hashed_pw = bcrypt.hashpw(contraseña.encode('utf-8'), salt)
    sql = """
        INSERT INTO usuarios (nombre, apellido, correo, usuario, contraseña, rol, fecha_creacion)
        VALUES (%s, %s, %s, %s, %s, %s, NOW())
    """
    cursor.execute(sql, (nombre, apellido, correo, usuario, hashed_pw.decode('utf-8'), rol))
    conn.commit()
    id_usuario = cursor.lastrowid
    cursor.close()
    conn.close()
    return id_usuario

# Autenticación de usuario
def autenticar_usuario(usuario, contraseña):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT * FROM usuarios WHERE usuario = %s"
    cursor.execute(sql, (usuario,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    if user and bcrypt.checkpw(contraseña.encode("utf-8"), user["contraseña"].encode("utf-8")):
        return user
    return None

# Listar usuarios (solo para pruebas)
def listar_usuarios():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT id_usuario, nombre, apellido, correo, usuario, rol, fecha_creacion FROM usuarios"
    cursor.execute(sql)
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users

def obtener_usuario_por_correo(correo: str):
    """
    Devuelve los datos del usuario a partir del correo, incluyendo id y contraseña hash.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT id_usuario, nombre, apellido, correo, usuario, contraseña, rol FROM usuarios WHERE correo = %s"
    cursor.execute(sql, (correo,))
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()
    return usuario

def obtener_usuario_por_id(id_usuario: int):
    """
    Devuelve información básica del usuario a partir del id.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT id_usuario, nombre, apellido, correo, usuario, rol FROM usuarios WHERE id_usuario = %s"
    cursor.execute(sql, (id_usuario,))
    usuario = cursor.fetchone()
    cursor.close()
    conn.close()
    return usuario
