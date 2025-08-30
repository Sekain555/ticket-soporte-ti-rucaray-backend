from database import get_connection

# Agregar un registro al feed (comentario o actividad)
def agregar_comentario(id_ticket, tipo, id_usuario=None, detalle=None):
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO ticket_feed (id_ticket, tipo, id_usuario, detalle, fecha)
        VALUES (%s, %s, %s, %s, NOW())
    """
    cursor.execute(sql, (id_ticket, tipo, id_usuario, detalle))

    # Actualizar fecha de actualización del ticket
    cursor.execute(
        """
        UPDATE tickets
        SET fecha_actualizacion = NOW()
        WHERE id_ticket = %s
        """,
        (id_ticket,)
    )

    conn.commit()
    id_feed = cursor.lastrowid
    cursor.close()
    conn.close()
    return id_feed


# Listar feed de un ticket (cronológico descendente)
def listar_feed(id_ticket):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
        SELECT f.*, u.nombre AS nombre_usuario, u.apellido AS apellido_usuario
        FROM ticket_feed f
        LEFT JOIN usuarios u ON f.id_usuario = u.id_usuario
        WHERE f.id_ticket = %s
        ORDER BY f.fecha DESC
    """
    cursor.execute(sql, (id_ticket,))
    feed = cursor.fetchall()
    cursor.close()
    conn.close()
    return feed
