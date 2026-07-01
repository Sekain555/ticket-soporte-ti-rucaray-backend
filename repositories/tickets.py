from database import get_connection
from repositories.ticket_feed import agregar_comentario
from typing import Optional
from repositories import notificaciones as notif_repo


# Crear un nuevo ticket
def crear_ticket(
    id_usuario, titulo, descripcion, prioridad, dispositivo=None, tipo_problema=None
):
    if not titulo or not titulo.strip():
        raise ValueError("El título es obligatorio")
    if not descripcion or not descripcion.strip():
        raise ValueError("La descripción es obligatoria")
    if not prioridad or not prioridad.strip():
        raise ValueError("La prioridad es obligatoria")

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
            id_usuario,
            titulo,
            descripcion,
            tipo_problema,
            prioridad,
            dispositivo,
            tiempo_objetivo_horas,
            tiempo_objetivo_horas,
            tiempo_objetivo_horas,
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

    # Obtener tecnicos para notificar
    cursor.execute("SELECT id_usuario FROM usuarios WHERE rol IN ('admin', 'soporte')")
    tecnicos = [r['id_usuario'] for r in cursor.fetchall()]

    cursor.close()
    conn.close()

    notif_repo.notificar_usuarios(
        tecnicos, 'ticket_creado',
        f"Nuevo ticket #{id_ticket}: {titulo}",
        referencia_id=id_ticket, referencia_tipo='ticket'
    )
    
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
    search: Optional[str] = None,
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

        if search and search.strip():
            search_term = f"%{search.strip()}%"
            where_clauses.append(
                "(titulo LIKE %s OR descripcion LIKE %s OR CAST(id_ticket AS CHAR) LIKE %s)"
            )
            params.extend([search_term, search_term, search_term])

        count_sql = "SELECT COUNT(*) AS total FROM tickets t JOIN usuarios u ON t.id_usuario = u.id_usuario"
        if where_clauses:
            count_sql += " WHERE " + " AND ".join(where_clauses)
        cursor.execute(count_sql, tuple(params) if params else None)
        row = cursor.fetchone()
        total = row["total"] if row and "total" in row else 0

        base_sql = """
            SELECT t.*,
                u.nombre AS nombre_usuario,
                u.apellido AS apellido_usuario
            FROM tickets t
            JOIN usuarios u ON t.id_usuario = u.id_usuario
        """
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
        s.tiempo_minimo_horas AS sla_tiempo_minimo_horas,
        a.nombre AS nombre_asignado,
        a.apellido AS apellido_asignado
    FROM tickets t
    JOIN usuarios u ON t.id_usuario = u.id_usuario
    LEFT JOIN sla_tipos_problema s ON t.tipo_problema = s.tipo_problema AND s.activo = 1
    LEFT JOIN usuarios a ON t.id_asignado = a.id_usuario
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
        "SELECT estado, fecha_creacion, fecha_limite_resolucion, id_usuario, id_asignado FROM tickets WHERE id_ticket = %s",
        (id_ticket,),
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
                (fecha_creacion, fecha_cierre),
            )
            tiempo_real_horas = cursor.fetchone()["horas"]
            resultado_sla = (
                "dentro_plazo" if fecha_cierre <= fecha_limite else "fuera_plazo"
            )

        cursor.execute(
            """
            INSERT INTO sla_cumplimiento (id_ticket, fecha_cierre, fecha_limite, tiempo_real_horas, resultado)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (id_ticket, fecha_cierre, fecha_limite, tiempo_real_horas, resultado_sla),
        )

    conn.commit()

    destinatarios = list({ticket['id_usuario'], ticket.get('id_asignado')} - {None, id_usuario})

    cursor.close()
    conn.close()

    notif_repo.notificar_usuarios(
        destinatarios, 'cambio_estado',
        f"Ticket #{id_ticket} actualizado a: {nuevo_estado}",
        referencia_id=id_ticket, referencia_tipo='ticket'
    )

    return resultado_sla


def actualizar_tipo_problema_ticket(id_ticket, nuevo_tipo_problema, id_usuario, rol):
    if rol not in ("admin", "soporte"):
        raise PermissionError("No autorizado")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT tipo_problema, fecha_creacion FROM tickets WHERE id_ticket = %s",
        (id_ticket,),
    )
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
            tiempo_objetivo_horas,
            fecha_creacion,
            tiempo_objetivo_horas,
            id_ticket,
        ),
    )

    detalle_feed = (
        f"Categoría actualizada: {tipo_anterior or 'pendiente'} → {nuevo_tipo_problema}"
    )
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


def editar_ticket(id_ticket: int, campos: dict, id_usuario: int, rol: str):
    CAMPOS_ADMIN = {
        "titulo",
        "descripcion",
        "prioridad",
        "dispositivo",
        "tipo_problema",
    }
    CAMPOS_USUARIO = {"titulo", "descripcion", "dispositivo"}

    if rol in ("admin", "soporte"):
        campos_permitidos = CAMPOS_ADMIN
    else:
        campos_permitidos = CAMPOS_USUARIO

    campos_validos = {
        k: v for k, v in campos.items() if k in campos_permitidos and v is not None
    }
    if not campos_validos:
        raise ValueError("No hay campos válidos para actualizar")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT titulo, descripcion, prioridad, dispositivo, tipo_problema, estado, id_usuario, id_asignado FROM tickets WHERE id_ticket = %s",
        (id_ticket,),
    )
    ticket_actual = cursor.fetchone()
    if not ticket_actual:
        cursor.close()
        conn.close()
        raise ValueError(f"Ticket {id_ticket} no encontrado")

    # Usuarios solo pueden editar tickets abiertos
    if rol not in ("admin", "soporte") and ticket_actual["estado"] != "abierto":
        raise PermissionError("Solo puedes editar tickets abiertos")

    set_sql = ", ".join([f"{k} = %s" for k in campos_validos.keys()])
    valores = list(campos_validos.values()) + [id_ticket]

    cursor.execute(
        f"UPDATE tickets SET {set_sql}, fecha_actualizacion = NOW() WHERE id_ticket = %s",
        tuple(valores),
    )

    # Registrar en feed los cambios realizados
    cambios = []
    for campo, nuevo_valor in campos_validos.items():
        valor_anterior = ticket_actual.get(campo)
        if str(valor_anterior or "") != str(nuevo_valor or ""):
            cambios.append(f'{campo}: {valor_anterior or "vacío"} → {nuevo_valor}')

    if cambios:
        detalle = "Ticket editado | " + " | ".join(cambios)
        cursor.execute(
            "INSERT INTO ticket_feed (id_ticket, id_usuario, tipo, detalle, fecha) VALUES (%s, %s, %s, %s, NOW())",
            (id_ticket, id_usuario, "edicion", detalle),
        )

    # Si se cambió tipo_problema, recalcular SLA
    if "tipo_problema" in campos_validos:
        nuevo_tipo = campos_validos["tipo_problema"]
        cursor.execute(
            "SELECT tiempo_maximo_horas FROM sla_tipos_problema WHERE tipo_problema = %s AND activo = 1",
            (nuevo_tipo,),
        )
        sla = cursor.fetchone()
        tiempo_objetivo = sla["tiempo_maximo_horas"] if sla else None

        cursor.execute(
            """UPDATE tickets SET tipo_problema = %s, tiempo_objetivo_horas = %s,
               fecha_limite_resolucion = CASE WHEN %s IS NOT NULL
               THEN DATE_ADD(fecha_creacion, INTERVAL %s HOUR) ELSE NULL END
               WHERE id_ticket = %s""",
            (nuevo_tipo, tiempo_objetivo, tiempo_objetivo, tiempo_objetivo, id_ticket),
        )

    conn.commit()

    destinatarios = list({ticket_actual['id_usuario'], ticket_actual.get('id_asignado')} - {None, id_usuario})
    notif_repo.notificar_usuarios(
        destinatarios, 'ticket_editado',
        f"Ticket #{id_ticket} ha sido editado",
        referencia_id=id_ticket, referencia_tipo='ticket'
    )

    cursor.close()
    conn.close()
    return True

def asignar_ticket(id_ticket: int, id_asignado: Optional[int], id_usuario: int, rol: str, comentario: str = None):
    if rol not in ("admin", "soporte"):
        raise PermissionError("No autorizado para asignar tickets")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Verificar que el ticket existe
    cursor.execute(
        "SELECT id_ticket, id_asignado FROM tickets WHERE id_ticket = %s",
        (id_ticket,)
    )
    ticket = cursor.fetchone()
    if not ticket:
        cursor.close()
        conn.close()
        raise ValueError(f"Ticket {id_ticket} no encontrado")

    # Soporte solo puede asignarse a sí mismo
    if rol == "soporte" and id_asignado != id_usuario:
        cursor.close()
        conn.close()
        raise PermissionError("Soporte solo puede asignarse a sí mismo")

    # Obtener nombre del técnico asignado para el feed
    nombre_asignado = "Sin asignar"
    if id_asignado:
        cursor.execute(
            "SELECT nombre, apellido FROM usuarios WHERE id_usuario = %s",
            (id_asignado,)
        )
        tecnico = cursor.fetchone()
        if tecnico:
            nombre_asignado = f"{tecnico['nombre']} {tecnico['apellido']}"

    # Actualizar asignación
    cursor.execute(
        "UPDATE tickets SET id_asignado = %s, fecha_actualizacion = NOW() WHERE id_ticket = %s",
        (id_asignado, id_ticket)
    )

    # Registrar en feed
    detalle = f"Ticket asignado a: {nombre_asignado}"
    if comentario and comentario.strip():
        detalle += f" | {comentario.strip()}"

    cursor.execute(
        "INSERT INTO ticket_feed (id_ticket, id_usuario, tipo, detalle, fecha) VALUES (%s, %s, %s, %s, NOW())",
        (id_ticket, id_usuario, "asignacion", detalle)
    )

    conn.commit()

    if id_asignado and id_asignado != id_usuario:
        notif_repo.crear_notificacion(
            id_asignado, 'ticket_asignado',
            f"Se te ha asignado el ticket #{id_ticket}",
            referencia_id=id_ticket, referencia_tipo='ticket'
        )

    cursor.close()
    conn.close()
    return True
