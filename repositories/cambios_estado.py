from database import get_connection

# Registrar un cambio de estado en un ticket
def agregar_cambio_estado(id_ticket, id_usuario, estado_anterior, estado_nuevo):
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO cambios_estado (id_ticket, id_usuario, estado_anterior, estado_nuevo, fecha_cambio)
        VALUES (%s, %s, %s, %s, NOW())
    """
    cursor.execute(sql, (id_ticket, id_usuario, estado_anterior, estado_nuevo))
    conn.commit()
    id_cambio = cursor.lastrowid
    cursor.close()
    conn.close()
    return id_cambio

# Listar cambios de estado de un ticket
def listar_cambios_estado(id_ticket):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    sql = "SELECT * FROM cambios_estado WHERE id_ticket = %s ORDER BY fecha_cambio ASC"
    cursor.execute(sql, (id_ticket,))
    cambios = cursor.fetchall()
    cursor.close()
    conn.close()
    return cambios
