from database import get_connection
from repositories.ticket_feed import agregar_comentario
from typing import Optional


# Crear un nuevo ticket
def crear_ticket(
    id_usuario, titulo, descripcion, prioridad, dispositivo=None, tipo_problema=None
):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Obtener SLA para el tipo de problema
    tiempo_objetivo_horas = None
    fecha_limite_resolucion = None

    if tipo_problema:
        cursor.execute(
            """
            SELECT tiempo_maximo_horas
            FROM sla_tipos_problema
            WHERE tipo_problema = %s AND activo = 1
            """,
            (tipo_problema,),
        )
        sla = cursor.fetchone()
        if sla:
            tiempo_objetivo_horas = sla["tiempo_maximo_horas"]

    # Insertar ticket
    sql = """
        INSERT INTO tickets (
            id_usuario, titulo, descripcion, tipo_problema, prioridad, dispositivo,
            estado, fecha_creacion, fecha_actualizacion,
            tiempo_objetivo_horas, fecha_limite_resolucion
        )
        VALUES (
            %s, %s, %s, %s, %s, %s,
            'abierto', NOW(), NOW(),
            %s,
            CASE WHEN %s IS NOT NULL THEN DATE_ADD(NOW(), INTERVAL %s HOUR) ELSE NULL END
        )
    """
    cursor.execute(
        sql,
        (
            id_usuario, titulo, descripcion, tipo_problema, prioridad, dispositivo,
            tiempo_objetivo_horas,
            tiempo_objetivo_horas, tiempo_objetivo_horas,
        ),
    )
    conn.commit()
    id_ticket = cursor.lastrowid

    # Insertar en el feed
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
def listar_tickets(
    rol,
    id_usuario,
    sort_by=None,
    order=None,
    estado: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
):
    conn = None
    cursor = None
    tickets = []
    total = 0

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

        count_sql = "SELECT COUNT(*) AS total FROM tickets"
        if where_clauses:
            count_sql += " WHERE " + " AND ".join(where_clauses)
        cursor.execute(count_sql, tuple(params) if params else None)
        row = cursor.fetchone()
        total = row["total"] if row and "total" in row else 0

        base_sql = "SELECT * FROM tickets"
        if where_clauses:
            base_sql += " WHERE " + " AND ".join(where_clauses)

        sql = base_sql + ORDER_BY + " LIMIT %s OFFSET %s"
        params_items = list(params)
        params_items.extend([limit, offset])

        cursor.execute(sql, tuple(params_items))
        tickets = cursor.fetchall()

    except Exception as e:
        print("❌ Error listando tickets:", e)
        tickets = []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return {"tickets": tickets, "total": total, "limit": limit, "offset": offset}


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

def actualizar_tipo_problema_ticket(id_ticket, nuevo_tipo_problema, id_usuario, rol):
    # Permiso backend (obligatorio)
    if rol not in ("admin", "soporte"):
        raise PermissionError("No autorizado")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Verificar ticket existe y obtener tipo anterior
    cursor.execute("SELECT tipo_problema FROM tickets WHERE id_ticket = %s", (id_ticket,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        raise ValueError(f"Ticket {id_ticket} no encontrado")

    tipo_anterior = row["tipo_problema"]

    # Update
    cursor.execute(
        """
        UPDATE tickets
        SET tipo_problema = %s, fecha_actualizacion = NOW()
        WHERE id_ticket = %s
        """,
        (nuevo_tipo_problema, id_ticket),
    )

    # Feed
    detalle_feed = f"Categoría actualizada: {tipo_anterior or 'pendiente'} → {nuevo_tipo_problema}"
    cursor.execute(
        """
        INSERT INTO ticket_feed (id_ticket, id_usuario, tipo, detalle, fecha)
        VALUES (%s, %s, %s, %s, NOW())
        """,
        (id_ticket, id_usuario, "cambio_categoria", detalle_feed),
    )

    conn.commit()
    cursor.close()
    conn.close()
    return True