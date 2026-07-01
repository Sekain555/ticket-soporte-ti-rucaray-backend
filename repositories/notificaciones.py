from database import get_connection
from typing import Optional


def crear_notificacion(
    id_usuario: int,
    tipo: str,
    mensaje: str,
    referencia_id: Optional[int] = None,
    referencia_tipo: Optional[str] = None,
):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO notificaciones (id_usuario, tipo, mensaje, referencia_id, referencia_tipo, fecha)
        VALUES (%s, %s, %s, %s, %s, NOW())
        """,
        (id_usuario, tipo, mensaje, referencia_id, referencia_tipo),
    )
    conn.commit()
    cursor.close()
    conn.close()


def notificar_usuarios(
    id_usuarios: list,
    tipo: str,
    mensaje: str,
    referencia_id: Optional[int] = None,
    referencia_tipo: Optional[str] = None,
):
    """Crea notificaciones para múltiples usuarios de una sola vez."""
    if not id_usuarios:
        return
    conn = get_connection()
    cursor = conn.cursor()
    valores = [
        (id_u, tipo, mensaje, referencia_id, referencia_tipo)
        for id_u in id_usuarios
    ]
    cursor.executemany(
        """
        INSERT INTO notificaciones (id_usuario, tipo, mensaje, referencia_id, referencia_tipo, fecha)
        VALUES (%s, %s, %s, %s, %s, NOW())
        """,
        valores,
    )
    conn.commit()
    cursor.close()
    conn.close()


def listar_notificaciones(id_usuario: int, solo_no_leidas: bool = False):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    if solo_no_leidas:
        cursor.execute(
            """
            SELECT * FROM notificaciones
            WHERE id_usuario = %s AND leida = 0
            ORDER BY fecha DESC
            """,
            (id_usuario,),
        )
    else:
        cursor.execute(
            """
            SELECT * FROM notificaciones
            WHERE id_usuario = %s
            ORDER BY fecha DESC
            LIMIT 50
            """,
            (id_usuario,),
        )
    result = cursor.fetchall()
    for n in result:
        if n.get('fecha') and not isinstance(n['fecha'], str):
            n['fecha'] = str(n['fecha'])
    cursor.close()
    conn.close()
    return result


def contar_no_leidas(id_usuario: int) -> int:
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT COUNT(*) AS total FROM notificaciones WHERE id_usuario = %s AND leida = 0",
        (id_usuario,),
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row['total'] if row else 0


def marcar_leidas(id_usuario: int, id_notificacion: Optional[int] = None):
    """Marca como leída una notificación específica o todas las del usuario."""
    conn = get_connection()
    cursor = conn.cursor()
    if id_notificacion:
        cursor.execute(
            "UPDATE notificaciones SET leida = 1 WHERE id_notificacion = %s AND id_usuario = %s",
            (id_notificacion, id_usuario),
        )
    else:
        cursor.execute(
            "UPDATE notificaciones SET leida = 1 WHERE id_usuario = %s",
            (id_usuario,),
        )
    conn.commit()
    cursor.close()
    conn.close()