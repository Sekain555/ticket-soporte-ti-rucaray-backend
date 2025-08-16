from database import get_connection

# Agregar un comentario a un ticket
def agregar_comentario(id_ticket, id_usuario, comentario, archivo_adjunto=None):
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO comentarios (id_ticket, id_usuario, comentario, archivo_adjunto, fecha)
        VALUES (%s, %s, %s, %s, NOW())
    """
    cursor.execute(sql, (id_ticket, id_usuario, comentario, archivo_adjunto))
    conn.commit()
    id_comentario = cursor.lastrowid
    cursor.close()
    conn.close()
    return id_comentario

# Listar comentarios de un ticket
def listar_comentarios(id_ticket):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT * FROM comentarios WHERE id_ticket = %s ORDER BY fecha ASC"
    cursor.execute(sql, (id_ticket,))
    comentarios = cursor.fetchall()
    cursor.close()
    conn.close()
    return comentarios
