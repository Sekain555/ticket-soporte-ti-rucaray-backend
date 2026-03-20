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

    ESTADOS_MAP = {
        "abierto": "abierto",
        "en_progreso": "en progreso",
        "resuelto": "resuelto",
        "cerrado": "cerrado",
    }

    def _order_by_clause(sort_by_val, order_val):
        col_key = (sort_by_val or "fecha_creacion").strip()
        direction = (order_val or "desc").strip().lower()

        ORDER_COLUMNS = {
            "fecha_creacion": "fecha_creacion",
            "fecha_actualizacion": "fecha_actualizacion",
            "id_ticket": "id_ticket",
            "prioridad": "CASE prioridad WHEN 'alta' THEN 3 WHEN 'media' THEN 2 WHEN 'baja' THEN 1 ELSE 0 END",
        }

        col_expr = ORDER_COLUMNS.get(col_key, "fecha_creacion")
        dir_sql = "DESC" if direction == "desc" else "ASC"

        return f" ORDER BY {col_expr} {dir_sql}, id_ticket DESC "

    ORDER_BY = _order_by_clause(sort_by, order)

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        where_clauses = []
        params = []

        if rol not in ("admin", "soporte"):
            where_clauses.append("id_usuario = %s")
            params.append(id_usuario)

        if estado:
            estado = estado.strip().lower()
            db_estado = ESTADOS_MAP.get(estado)
            if db_estado:
                where_clauses.append("estado = %s")
                params.append(db_estado)

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
        u.puesto AS puesto_usuario,
        s.tiempo_minimo_horas AS sla_tiempo_minimo_horas
    FROM tickets t
    JOIN usuarios u ON t.id_usuario = u.id_usuario
    LEFT JOIN sla_tipos_problema s ON t.tipo_problema = s.tipo_problema AND s.activo = 1
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

    # Obtener datos actuales del ticket
    cursor.execute(
        "SELECT estado, fecha_creacion, fecha_limite_resolucion FROM tickets WHERE id_ticket = %s",
        (id_ticket,)
    )
    ticket = cursor.fetchone()
    if not ticket:
        cursor.close()
        conn.close()
        raise ValueError(f"Ticket {id_ticket} no encontrado")

    estado_anterior = ticket["estado"]

    # Actualizar estado
    cursor.execute(
        """
        UPDATE tickets
        SET estado = %s, fecha_actualizacion = NOW()
        WHERE id_ticket = %s
        """,
        (nuevo_estado, id_ticket),
    )

    # Registrar en cambios_estado
    cursor.execute(
        """
        INSERT INTO cambios_estado (id_ticket, estado_anterior, estado_nuevo, id_usuario, fecha_cambio)
        VALUES (%s, %s, %s, %s, NOW())
        """,
        (id_ticket, estado_anterior, nuevo_estado, id_usuario),
    )

    # Feed
    if comentario and comentario.strip():
        detalle_feed = f"Ticket {nuevo_estado} | {comentario.strip()}"
    else:
        detalle_feed = f"Ticket {nuevo_estado}"

    cursor.execute(
        """
        INSERT INTO ticket_feed (id_ticket, id_usuario, tipo, detalle, fecha)
        VALUES (%s, %s, %s, %s, NOW())
        """,
        (id_ticket, id_usuario, "cambio_estado", detalle_feed),
    )

    # Evaluación de cumplimiento SLA al cerrar
    resultado_sla = None
    if nuevo_estado == "cerrado":
        fecha_creacion = ticket["fecha_creacion"]
        fecha_limite = ticket["fecha_limite_resolucion"]

        cursor.execute("SELECT NOW() AS ahora")
        fecha_cierre = cursor.fetchone()["ahora"]

        if fecha_limite is None:
            resultado_sla = "sin_sla"
            tiempo_real_horas = None
        else:
            cursor.execute(
                "SELECT TIMESTAMPDIFF(SECOND, %s, %s) / 3600.0 AS horas",
                (fecha_creacion, fecha_cierre)
            )
            tiempo_real_horas = cursor.fetchone()["horas"]
            resultado_sla = "dentro_plazo" if fecha_cierre <= fecha_limite else "fuera_plazo"

        cursor.execute(
            """
            INSERT INTO sla_cumplimiento (id_ticket, fecha_cierre, fecha_limite, tiempo_real_horas, resultado)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (id_ticket, fecha_cierre, fecha_limite, tiempo_real_horas, resultado_sla)
        )

    conn.commit()
    cursor.close()
    conn.close()
    return resultado_sla


def actualizar_tipo_problema_ticket(id_ticket, nuevo_tipo_problema, id_usuario, rol):
    if rol not in ("admin", "soporte"):
        raise PermissionError("No autorizado")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT tipo_problema, fecha_creacion FROM tickets WHERE id_ticket = %s", (id_ticket,))
    row = cursor.fetchone()
    if not row:
        cursor.close()
        conn.close()
        raise ValueError(f"Ticket {id_ticket} no encontrado")

    tipo_anterior = row["tipo_problema"]
    fecha_creacion = row["fecha_creacion"]

    # Obtener nuevo SLA
    cursor.execute(
        """
        SELECT tiempo_maximo_horas
        FROM sla_tipos_problema
        WHERE tipo_problema = %s AND activo = 1
        """,
        (nuevo_tipo_problema,),
    )
    sla = cursor.fetchone()
    tiempo_objetivo_horas = sla["tiempo_maximo_horas"] if sla else None

    # Actualizar tipo_problema + recalcular SLA
    cursor.execute(
        """
        UPDATE tickets
        SET tipo_problema = %s,
            tiempo_objetivo_horas = %s,
            fecha_limite_resolucion = CASE
                WHEN %s IS NOT NULL THEN DATE_ADD(%s, INTERVAL %s HOUR)
                ELSE NULL
            END,
            fecha_actualizacion = NOW()
        WHERE id_ticket = %s
        """,
        (
            nuevo_tipo_problema,
            tiempo_objetivo_horas,
            tiempo_objetivo_horas, fecha_creacion, tiempo_objetivo_horas,
            id_ticket,
        ),
    )

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