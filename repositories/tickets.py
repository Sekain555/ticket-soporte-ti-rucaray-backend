from database import get_connection

# Crear un nuevo ticket
def crear_ticket(id_usuario, titulo, descripcion, tipo_problema, prioridad, dispositivo=None):
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO tickets (id_usuario, titulo, descripcion, tipo_problema, prioridad, dispositivo, estado, fecha_creacion, fecha_actualizacion)
        VALUES (%s, %s, %s, %s, %s, %s, 'abierto', NOW(), NOW())
    """
    cursor.execute(sql, (id_usuario, titulo, descripcion, tipo_problema, prioridad, dispositivo))
    conn.commit()
    id_ticket = cursor.lastrowid
    cursor.close()
    conn.close()
    return id_ticket

# Listar tickets (opcionalmente por usuario)
def listar_tickets(id_usuario=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    if id_usuario:
        sql = "SELECT * FROM tickets WHERE id_usuario = %s ORDER BY fecha_creacion DESC"
        cursor.execute(sql, (id_usuario,))
    else:
        sql = "SELECT * FROM tickets ORDER BY fecha_creacion DESC"
        cursor.execute(sql)
    tickets = cursor.fetchall()
    cursor.close()
    conn.close()
    return tickets

# Obtener detalles de un ticket
def obtener_ticket(id_ticket):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT * FROM tickets WHERE id_ticket = %s"
    cursor.execute(sql, (id_ticket,))
    ticket = cursor.fetchone()
    cursor.close()
    conn.close()
    return ticket

# Actualizar estado de un ticket
def actualizar_estado_ticket(id_ticket, nuevo_estado):
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
        UPDATE tickets
        SET estado = %s, fecha_actualizacion = NOW()
        WHERE id_ticket = %s
    """
    cursor.execute(sql, (nuevo_estado, id_ticket))
    conn.commit()
    cursor.close()
    conn.close()
    return True
