from database import get_connection
from typing import Optional
from datetime import timedelta


def serializar_mantencion(m: dict) -> dict:
    """Convierte campos no serializables (timedelta, date) a string."""
    if not m:
        return m
    for campo in ('hora_inicio', 'hora_fin'):
        if isinstance(m.get(campo), timedelta):
            total = int(m[campo].total_seconds())
            horas = total // 3600
            minutos = (total % 3600) // 60
            m[campo] = f"{horas:02d}:{minutos:02d}"
    for campo in ('fecha_propuesta', 'fecha_creacion', 'fecha_actualizacion'):
        if m.get(campo) is not None and not isinstance(m[campo], str):
            m[campo] = str(m[campo])
    return m


# Crear una nueva mantención
def crear_mantencion(
    id_usuario_solicitante: int,
    titulo: str,
    descripcion: Optional[str],
    fecha_propuesta: str,
    hora_inicio: str,
    hora_fin: str,
):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Validar conflicto de horario
    # Traslape ocurre cuando: hora_inicio_nueva < hora_fin_existente
    #                     AND hora_fin_nueva > hora_inicio_existente
    cursor.execute(
        """
        SELECT id_mantencion, titulo, hora_inicio, hora_fin
        FROM mantenciones
        WHERE fecha_propuesta = %s
          AND estado != 'cancelado'
          AND %s < hora_fin
          AND %s > hora_inicio
        LIMIT 1
        """,
        (fecha_propuesta, hora_inicio, hora_fin),
    )
    conflicto = cursor.fetchone()
    if conflicto:
        conflicto = serializar_mantencion(conflicto)
        cursor.close()
        conn.close()
        raise ValueError(
            f"Conflicto de horario con la mantención #{conflicto['id_mantencion']} "
            f"'{conflicto['titulo']}' "
            f"({conflicto['hora_inicio']} - {conflicto['hora_fin']})"
        )

    cursor.execute(
        """
        INSERT INTO mantenciones (
            titulo, descripcion, id_usuario_solicitante,
            fecha_propuesta, hora_inicio, hora_fin,
            estado, fecha_creacion, fecha_actualizacion
        )
        VALUES (%s, %s, %s, %s, %s, %s, 'propuesto', NOW(), NOW())
        """,
        (titulo, descripcion, id_usuario_solicitante,
         fecha_propuesta, hora_inicio, hora_fin),
    )
    conn.commit()
    id_mantencion = cursor.lastrowid
    cursor.close()
    conn.close()
    return id_mantencion


# Listar mantenciones — admin/soporte ven todas, usuario solo las propias
def listar_mantenciones(
    rol: str,
    id_usuario: int,
    estado: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
):
    conn = None
    cursor = None
    result = []
    total = 0

    ESTADOS_VALIDOS = {'propuesto', 'confirmado', 'reprogramado', 'cancelado'}

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        where_clauses = []
        params = []

        if rol not in ('admin', 'soporte'):
            where_clauses.append('m.id_usuario_solicitante = %s')
            params.append(id_usuario)

        if estado and estado.strip().lower() in ESTADOS_VALIDOS:
            where_clauses.append('m.estado = %s')
            params.append(estado.strip().lower())

        where_sql = ('WHERE ' + ' AND '.join(where_clauses)) if where_clauses else ''

        base_sql = f"""
            SELECT
                m.*,
                us.nombre AS nombre_solicitante,
                us.apellido AS apellido_solicitante,
                ua.nombre AS nombre_asignado,
                ua.apellido AS apellido_asignado
            FROM mantenciones m
            JOIN usuarios us ON m.id_usuario_solicitante = us.id_usuario
            LEFT JOIN usuarios ua ON m.id_usuario_asignado = ua.id_usuario
            {where_sql}
        """

        # Total
        count_sql = f"SELECT COUNT(*) AS total FROM mantenciones m {where_sql}"
        cursor.execute(count_sql, tuple(params) if params else None)
        row = cursor.fetchone()
        total = row['total'] if row else 0

        # Listado paginado
        cursor.execute(
            base_sql + ' ORDER BY m.fecha_propuesta ASC, m.hora_inicio ASC LIMIT %s OFFSET %s',
            tuple(params) + (limit, offset),
        )
        result = [serializar_mantencion(m) for m in cursor.fetchall()]

    except Exception as e:
        print('❌ Error listando mantenciones:', e)
        result = []

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return {'mantenciones': result, 'total': total, 'limit': limit, 'offset': offset}


# Obtener mantención por ID
def obtener_mantencion(id_mantencion: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            m.*,
            us.nombre AS nombre_solicitante,
            us.apellido AS apellido_solicitante,
            us.departamento AS departamento_solicitante,
            us.puesto AS puesto_solicitante,
            ua.nombre AS nombre_asignado,
            ua.apellido AS apellido_asignado
        FROM mantenciones m
        JOIN usuarios us ON m.id_usuario_solicitante = us.id_usuario
        LEFT JOIN usuarios ua ON m.id_usuario_asignado = ua.id_usuario
        WHERE m.id_mantencion = %s
        """,
        (id_mantencion,),
    )
    mantencion = serializar_mantencion(cursor.fetchone())
    cursor.close()
    conn.close()
    return mantencion


# Actualizar estado de una mantención (solo admin/soporte)
def actualizar_estado_mantencion(
    id_mantencion: int,
    nuevo_estado: str,
    id_usuario: int,
    rol: str,
    notas_soporte: Optional[str] = None,
):
    if rol not in ('admin', 'soporte'):
        raise PermissionError('No autorizado')

    ESTADOS_VALIDOS = {'propuesto', 'confirmado', 'reprogramado', 'cancelado'}
    if nuevo_estado not in ESTADOS_VALIDOS:
        raise ValueError(f'Estado inválido: {nuevo_estado}')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        'SELECT id_mantencion FROM mantenciones WHERE id_mantencion = %s',
        (id_mantencion,)
    )
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        raise ValueError(f'Mantención {id_mantencion} no encontrada')

    cursor.execute(
        """
        UPDATE mantenciones
        SET estado = %s,
            notas_soporte = COALESCE(%s, notas_soporte),
            fecha_actualizacion = NOW()
        WHERE id_mantencion = %s
        """,
        (nuevo_estado, notas_soporte, id_mantencion),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True