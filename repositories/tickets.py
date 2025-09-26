from database import get_connection
from repositories.ticket_feed import agregar_comentario
from typing import Optional


# Crear un nuevo ticket
def crear_ticket(
    id_usuario, titulo, descripcion, tipo_problema, prioridad, dispositivo=None
):
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        INSERT INTO tickets (id_usuario, titulo, descripcion, tipo_problema, prioridad, dispositivo, estado, fecha_creacion, fecha_actualizacion)
        VALUES (%s, %s, %s, %s, %s, %s, 'abierto', NOW(), NOW())
    """
    cursor.execute(
        sql, (id_usuario, titulo, descripcion, tipo_problema, prioridad, dispositivo)
    )
    conn.commit()
    id_ticket = cursor.lastrowid

    # Insertar comentario en el feed
    sql_feed = """
        INSERT INTO ticket_feed (id_ticket, id_usuario, tipo, detalle, fecha)
        VALUES (%s, %s, %s, %s, NOW())
    """
    cursor.execute(
        sql_feed, (id_ticket, id_usuario, "creacion_ticket", "Ticket creado")
    )
    conn.commit()

    cursor.close()
    conn.close()
    return id_ticket


# Listar tickets
def listar_tickets(rol, id_usuario, sort_by=None, order=None, estado: Optional[str] = None):
    conn = None
    cursor = None
    tickets = []

    # Lista blanca de estados permitidos
    ESTADOS_MAP = {
        "abierto": "abierto",
        "en_progreso": "en progreso",
        "resuelto": "resuelto",
        "cerrado": "cerrado",
    }

    def _order_by_clause(sort_by_val, order_val):
        col_key = (sort_by_val or "fecha_creacion").strip()
        direction = (order_val or "desc").strip().lower()

        # Lista blanca de columnas/expresiones permitidas
        ORDER_COLUMNS = {
            "fecha_creacion": "fecha_creacion",
            "fecha_actualizacion": "fecha_actualizacion",
            "id_ticket": "id_ticket",
            "prioridad": "CASE prioridad WHEN 'alta' THEN 3 WHEN 'media' THEN 2 WHEN 'baja' THEN 1 ELSE 0 END",
        }

        col_expr = ORDER_COLUMNS.get(col_key, "fecha_creacion")
        dir_sql = "DESC" if direction == "desc" else "ASC"

        # Tiebreak para orden estable
        return f" ORDER BY {col_expr} {dir_sql}, id_ticket DESC "
    
    ORDER_BY = _order_by_clause(sort_by, order)

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        where_clauses = []
        params = []

        # Control por rol: los usuarios "normales" solo ven sus tickets
        if rol not in ("admin", "soporte"):
            where_clauses.append("id_usuario = %s")
            params.append(id_usuario)

        # Filtro por estado (si viene uno válido)
        if estado:
            estado = estado.strip().lower()
            db_estado = ESTADOS_MAP.get(estado)  # None si no es válido
            if db_estado:
                where_clauses.append("estado = %s")
                params.append(db_estado)
            # Si no es válido, simplemente no filtramos por estado (fail-safe)

        base_sql = "SELECT * FROM tickets"
        if where_clauses:
            base_sql += " WHERE " + " AND ".join(where_clauses)

        sql = base_sql + ORDER_BY
        cursor.execute(sql, tuple(params) if params else None)

        tickets = cursor.fetchall()

    except Exception as e:
        print("❌ Error listando tickets:", e)
        tickets = []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return tickets


# Obtener detalles de un ticket
def obtener_ticket(id_ticket):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    sql = """
    SELECT 
        t.*, 
        u.nombre AS nombre_usuario, 
        u.apellido AS apellido_usuario,
        u.departamento AS departamento_usuario,
        u.puesto AS puesto_usuario
    FROM tickets t
    JOIN usuarios u ON t.id_usuario = u.id_usuario
    WHERE t.id_ticket = %s
    """
    cursor.execute(sql, (id_ticket,))
    ticket = cursor.fetchone()
    cursor.close()
    conn.close()
    return ticket


# Actualizar estado de un ticket
def actualizar_estado_ticket(id_ticket, nuevo_estado, id_usuario, comentario=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Obtener estado actual
    cursor.execute("SELECT estado FROM tickets WHERE id_ticket = %s", (id_ticket,))
    ticket = cursor.fetchone()
    if not ticket:
        cursor.close()
        conn.close()
        raise ValueError(f"Ticket {id_ticket} no encontrado")

    estado_anterior = ticket["estado"]

    # Actualizar estado en tickets
    cursor.execute(
        """
        UPDATE tickets
        SET estado = %s, fecha_actualizacion = NOW()
        WHERE id_ticket = %s
        """,
        (nuevo_estado, id_ticket),
    )

    # Registrar cambio en cambios_estado
    cursor.execute(
        """
        INSERT INTO cambios_estado (id_ticket, estado_anterior, estado_nuevo, id_usuario, fecha_cambio)
        VALUES (%s, %s, %s, %s, NOW())
        """,
        (id_ticket, estado_anterior, nuevo_estado, id_usuario),
    )

    # Preparar comentario para el feed
    if comentario and comentario.strip():
        detalle_feed = f"Ticket {nuevo_estado} | {comentario.strip()}"
    else:
        detalle_feed = f"Ticket {nuevo_estado}"

    # Insertar comentario en el feed
    sql_feed = """
        INSERT INTO ticket_feed (id_ticket, id_usuario, tipo, detalle, fecha)
        VALUES (%s, %s, %s, %s, NOW())
    """
    cursor.execute(sql_feed, (id_ticket, id_usuario, "cambio_estado", detalle_feed))

    conn.commit()
    cursor.close()
    conn.close()
    return True
