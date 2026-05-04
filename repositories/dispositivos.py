from database import get_connection
from typing import Optional


def serializar_dispositivo(d: dict) -> dict:
    """Convierte campos no serializables a string."""
    if not d:
        return d
    for campo in ('fecha_registro', 'fecha_actualizacion'):
        if d.get(campo) is not None and not isinstance(d[campo], str):
            d[campo] = str(d[campo])
    return d


def listar_dispositivos(
    tipo: Optional[str] = None,
    area: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    where_clauses = []
    params = []

    if tipo:
        where_clauses.append('tipo_equipo = %s')
        params.append(tipo)
    if area:
        where_clauses.append('area LIKE %s')
        params.append(f'%{area}%')

    where_sql = ('WHERE ' + ' AND '.join(where_clauses)) if where_clauses else ''

    cursor.execute(
        f'SELECT COUNT(*) AS total FROM dispositivos {where_sql}',
        tuple(params) if params else None
    )
    total = cursor.fetchone()['total']

    cursor.execute(
        f'SELECT * FROM dispositivos {where_sql} ORDER BY area ASC, nombre_asignado ASC LIMIT %s OFFSET %s',
        tuple(params) + (limit, offset)
    )
    result = [serializar_dispositivo(d) for d in cursor.fetchall()]

    cursor.close()
    conn.close()
    return {'dispositivos': result, 'total': total, 'limit': limit, 'offset': offset}


def obtener_dispositivo(id_dispositivo: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        'SELECT * FROM dispositivos WHERE id_dispositivo = %s',
        (id_dispositivo,)
    )
    dispositivo = serializar_dispositivo(cursor.fetchone())
    cursor.close()
    conn.close()
    return dispositivo


def crear_dispositivo(data: dict) -> int:
    CAMPOS = [
        'nombre_asignado', 'area', 'tipo_equipo', 'marca', 'procesador',
        'ram', 'disco_duro', 'monitor', 'antivirus', 'rj45', 'tipo_lan',
        'direccion_ip', 'mac_wifi', 'version_windows', 'tipo_office',
        'nombre_equipo', 'dominio', 'observaciones',
    ]
    campos_presentes = {k: v for k, v in data.items() if k in CAMPOS}

    if 'tipo_equipo' not in campos_presentes or not campos_presentes['tipo_equipo']:
        raise ValueError('tipo_equipo es obligatorio')

    cols = ', '.join(campos_presentes.keys())
    placeholders = ', '.join(['%s'] * len(campos_presentes))
    valores = tuple(campos_presentes.values())

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f'INSERT INTO dispositivos ({cols}) VALUES ({placeholders})',
        valores
    )
    conn.commit()
    id_dispositivo = cursor.lastrowid
    cursor.close()
    conn.close()
    return id_dispositivo


def actualizar_dispositivo(id_dispositivo: int, data: dict):
    CAMPOS = [
        'nombre_asignado', 'area', 'tipo_equipo', 'marca', 'procesador',
        'ram', 'disco_duro', 'monitor', 'antivirus', 'rj45', 'tipo_lan',
        'direccion_ip', 'mac_wifi', 'version_windows', 'tipo_office',
        'nombre_equipo', 'dominio', 'observaciones',
    ]
    campos_presentes = {k: v for k, v in data.items() if k in CAMPOS}

    if not campos_presentes:
        raise ValueError('No hay campos válidos para actualizar')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        'SELECT id_dispositivo FROM dispositivos WHERE id_dispositivo = %s',
        (id_dispositivo,)
    )
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        raise ValueError(f'Dispositivo {id_dispositivo} no encontrado')

    set_sql = ', '.join([f'{k} = %s' for k in campos_presentes.keys()])
    valores = tuple(campos_presentes.values()) + (id_dispositivo,)

    cursor.execute(
        f'UPDATE dispositivos SET {set_sql}, fecha_actualizacion = NOW() WHERE id_dispositivo = %s',
        valores
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True